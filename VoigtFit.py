#	Written by:
#	Jens-Kristian Krogager
#	PhD Student, Dark Cosmology Centre, Niels Bohr Institute
#	University of Copenhagen
#	
#	version 1.6
#	added smooth continuum definition
#
#	version 1.5
#	added 'copy_velocity_structure'
#	to anchor the line structure to a given ion
#
#	version 1.4
#	added subpixel profile fitting

import numpy as np, matplotlib.pyplot as plt
import pyfits as pf
from scipy import ndimage
import scipy.signal as signal
from scipy.optimize import curve_fit
import pickle
from lmfit import Parameters, minimize, report_fit, conf_interval, report_ci
import os
import copy
from voigt import evaluate_profile
from regions import Region
import output
from parse_input import parse_parameters
from argparse import ArgumentParser

options = {'nsamp':1,
		   'npad':20}
myfloat = np.float64

if os.environ.has_key('ATOMPATH'):
	atomfile = os.environ['ATOMPATH']

else:
	print("No ATOMPATH in environment ... Using static provided atomic database ...")
	atomfile = "static/atomdata_updated.dat"
	# atomfile = raw_input("No atomic database was found!\nSpecify filename here:")

lineList = np.loadtxt(atomfile, dtype=[('trans','S13'), ('ion','S6'), ('l0','f4'), ('f','f4'), ('gam','f4')])


def air2vac(air):
	### From Donald Morton 1991, ApJS 77,119
	if type(air) == float or type(air)==int:
		air = np.array(air)
	air = np.array(air)
	ij = (np.array(air) >= 2000)
	out = np.array(air).copy()
	sigma2 = (1.e4/air)**2
	#fact = 1.0 + 6.4328e-5 + 2.94981e-2/(146.0 - sigma2) + 2.5540e-4/( 41.0 - sigma2)
	fact = 1.0 + 6.4328e-5 + 2.94981e-2/(146.0 - sigma2) + 2.5540e-4/( 41.0 - sigma2)
	out[ij] = air[ij]*fact[ij]
	return out

def SaveDataSet(pickle_file, Object):
    f = open(pickle_file, 'wb')
    pickle.dump(Object, f)
    f.close()

def LoadDataSet(pickle_file):
    f = open(pickle_file, 'rb')
    Object = pickle.load(f)
    f.close()
    return Object


class Line(object):
	def __init__(self, tag, active=True):
		self.tag = tag
		index = lineList['trans'].tolist().index(tag)
		tag, ion, l0, f, gam = lineList[index]
		
		self.tag = tag
		self.ion = ion
		self.element = ion
		self.l0 = l0
		self.f = f
		self.gam = gam
		self.active = active
	
	def get_properties(self):
		return (self.l0, self.f, self.gam)

	def set_inactive(self):
		self.active = False

	def set_active(self):
		self.active = True



class DataSet(object):
	def __init__(self, z):
		# Define the systemic redshift
		self.redshift = z

		# container for data chunks to be fitted
		# data should be added by calling method 'add_data'
		self.data = []
		
		# container for absorption lines
		# each line is defined as a class 'Line'
		self.lines  = dict()		# a dictionary containing a Line class for each line-tag key
		self.all_lines  = list()	# a list containing all the line-tags defined. The same as lines.keys()

		# container for the fitting regions containing Lines
		# each region is defined as a class 'Region'
		self.regions = list()

		# Number of components in each ion
		self.components = dict()
		
		# Define default velocity span for fitting region
		self.velspan = 500.  # km/s

		self.ready2fit = False
		self.best_fit = None


	def add_data(self, wl, flux, res, err=None, normalized=False):
		"""
		Add spectral data chunk to Absorption Line System.

		 -- input --
		Give wavelength, flux and error as np.arrays.
		
		The spectrum should be helio-vacuum corrected!
		Flux and error should be given in the same units.

		The resolution 'res' of the spectrum should be specified in km/s
		"""
		if err is None:
			err = np.ones_like(flux)

		self.data.append({'wl':wl, 'flux':flux,
			'error':err, 'res':res, 'norm':normalized})

	def remove_line(self, tag):
		if tag in self.all_lines:
			self.all_lines.remove(tag)
			if tag in self.lines.keys():
				self.lines.pop(tag)
		
		### Check if the ion has transistions defined in other regions
		ion = tag.split('_')[0]
		ion_defined_elsewhere = False
		for line_tag in self.all_lines:
			if line_tag.find(ion)>=0:
				ion_defined_elsewhere = True

		### If it is not defined elsewhere, remove it from components
		if not ion_defined_elsewhere:
			self.components.pop(ion)

		remove_this = -1
		for num, region in enumerate(self.regions):
			if region.has_line(tag):
				remove_this = num
		
		if remove_this>=0:
			if len(self.regions[remove_this].lines)==1:
				self.regions.pop(remove_this)
			else:
				self.regions[remove_this].remove_line(tag)
		else:
			print ""
			print " The line is not defined. Nothing to remove."

	def find_line(self, tag):
		if tag in self.all_lines:
			for region in self.regions:
				if region.has_line(tag):
					return region
		
		else:
			print "\n The line (%s) is not defined."%tag

		return None


	def activate_line(self, line_tag):
		if line_tag in self.lines.keys():
			line = self.lines[line_tag]
			line.set_active()

		else:
			region = self.find_line(line_tag)
			for line in region.lines:
				if line.tag == line_tag:
					line.set_active()

	def deactivate_line(self, line_tag):
		if line_tag in self.lines.keys():
			line = self.lines[line_tag]
			line.set_inactive()

		else:
			region = self.find_line(line_tag)
			for line in region.lines:
				if line.tag == line_tag:
					line.set_inactive()
	
	def deactivate_all(self):
		for line_tag in self.all_lines:
			self.deactivate_line(line_tag)

	def activate_all(self):
		for line_tag in self.all_lines:
			self.activate_line(line_tag)


	def reset_components(self, element=None):
		"""	Reset components dictionary.
			If an element is given, only this element is reset.
			Otherwise all elements are reset."""

		if element:
			if element in self.components.keys():
				self.components.pop(element)
			else:
				print " [ERROR] - No components defined for element: %s" % element

		else:
			self.components = dict()

	def add_component(self, element, z, b, logN,
					  var_z=True, var_b=True, var_N=True, tie_z=None, tie_b=None):
		options = {'var_z':var_z, 'var_b':var_b, 'var_N':var_N, 'tie_z':tie_z, 'tie_b':tie_b}
		if self.components.has_key(element):
			self.components[element].append([z, b, logN, options])
		else:
			self.components[element]=[ [z, b, logN, options] ]

	def delete_component(self, element, index):
		"""
		Remove component with the given `index'.
		"""
		if self.components.has_key(element):
			self.components[element].pop(index)

		else:
			print " [ERROR] - No components defined for ion: "+element

	def copy_components(self, element, anchor, logN=0, ref_comp=0, tie_z=True, tie_b=True):
		"""
		Copy velocity structure from one element to another.
		Input: 'element' is the new ion to define, which will
				be linked to the ion 'anchor'.
				If logN is given the starting guess is defined
				from this value following the pattern of the
				component number 'ref_comp' of the anchor ion.
				
				If 'tie_z' or 'tie_b' is set, then *all* components
				of the new element will be linked to the anchor.
		"""
		reference = self.components[anchor]
		# overwrite the components already defined for element
		# if they exist.
		self.components[element] = []

		offset_N = logN - reference[ref_comp][2]
		for num, comp in enumerate(reference):
			new_comp = copy.deepcopy(comp)
			if logN:
				new_comp[2] += offset_N
			if tie_z:
				new_comp[3]['tie_z'] = 'z%i_%s'%(num, anchor)
			if tie_b:
				new_comp[3]['tie_b'] = 'b%i_%s'%(num, anchor)

			self.components[element].append(new_comp)


	def add_line(self, tag, velspan=500., active=True, norm_method=1):
		self.ready2fit = False
		if tag in self.all_lines:
			print " [WARNING] - Line is already defined."
			return False

		if tag in lineList['trans']:
			new_line = Line(tag)
		else:
			print "\nThe transition (%s) not found in line list!"%tag
			return False

		if not self.components.has_key(new_line.element):
			# Initiate component list if ion has not been defined before:
			self.components[new_line.element] = list()
		
		l_center = new_line.l0*(self.redshift + 1.)
		
		### Initiate new Region:
		new_region = Region(velspan, new_line)

		if self.data:
			success = False
			for chunk in self.data:
				if chunk['wl'].min() < l_center < chunk['wl'].max():
					wl	 = chunk['wl']
					vel  = (wl-l_center)/l_center*299792.
					span = ((vel >= -velspan)*(vel <= velspan)).nonzero()[0]
					new_wavelength = wl[span]

					# check if the line overlaps with another already defined region
					if len(self.regions)>0:
						merge = -1
						for num, region in enumerate(self.regions):
							if np.intersect1d(new_wavelength, region.wl).any():
								merge = num
						
						if merge >= 0:
							#if the regions overlap with another:
							#	merge the list of lines in the region
							new_region.lines += self.regions[merge].lines

							#	merge the wavelength region
							region_wl = np.union1d(new_wavelength, self.regions[merge].wl)

							#	and remove the overlapping region from the dataset
							self.regions.pop(merge)

						else:
							region_wl = new_wavelength

					else:
						region_wl = new_wavelength

					### wavelength has now been defined and merged
					### Cutout spectral chunks and add them to the Region
					cutout = (wl>=region_wl.min())*(wl<=region_wl.max())

					new_region.add_data_to_region(chunk, cutout)

					self.regions.append(new_region)
					self.all_lines.append(tag)
					self.lines[tag] = new_line
					success = True

			if not success:
				print "\n [ERROR] - The given line is not covered by the spectral data: "+tag
				print ""
				return False

		else:
			print " [ERROR]  No data is loaded. Run method 'add_data' to add spectral data."

	def add_many_lines(self, tags, velspans=None):
		self.ready2fit = False
		if velspans:
			assert len(tags)==len(velspans)
			for tag, velspan in zip(tags, velspans):
				self.add_line(tag, velspan)
		
		else:
			for tag in tags:
				self.add_line(tag, self.velspan)

	def prepare_dataset(self, verbose=True):
		### Prepare fitting regions to be fit:
		###	normalize spectral region
		
		plt.close('all')
		for region in self.regions:
			if not region.normalized:

				go_on = 0
				while go_on==0:
					go_on = region.normalize()
					# region.normalize returns 1 when continuum is fitted
		if verbose:
			print ""
			print " [DONE] - Continuum fitting successfully finished."
			print ""

		###	mask spectral regions that should not be fitted
		for region in self.regions:
			if region.new_mask:
				region.define_mask()
		if verbose:
			print ""
			print " [DONE] - Spectral masks successfully created."
			print ""


		### Prepare fit parameters  [class: lmfit.Parameters]
		self.pars = Parameters()
		# First setup parameters with values only:
		for ion in self.components.keys():
			for n, comp in enumerate(self.components[ion]):
				ion = ion.replace('*','x')
				z, b, logN, opts = comp
				z_name = 'z%i_%s'%(n, ion)
				b_name = 'b%i_%s'%(n, ion)
				N_name = 'logN%i_%s'%(n, ion)

				self.pars.add(z_name, value=myfloat(z), vary=opts['var_z'], min=0.)
				self.pars.add(b_name, value=myfloat(b), vary=opts['var_b'], min=0.)
				self.pars.add(N_name, value=myfloat(logN), vary=opts['var_N'], min=0.)

		# Then setup parameter links:
		for ion in self.components.keys():
			for n, comp in enumerate(self.components[ion]):
				ion = ion.replace('*','x')
				z, b, logN, opts = comp
				z_name = 'z%i_%s'%(n, ion)
				b_name = 'b%i_%s'%(n, ion)

				if opts['tie_z']:
					self.pars[z_name].expr = opts['tie_z']
				if opts['tie_b']:
					self.pars[b_name].expr = opts['tie_b']

		self.ready2fit = True

		### Check that all active elements have components defined:
		for line_tag in self.all_lines:
			ion = line_tag.split('_')[0]
			line = self.lines[line_tag]
			if not ion in self.components.keys() and line.active:
				print ""
				print " [ERROR] - Components are not defined for element: "+ion
				print ""
				self.ready2fit = False

				return False

		### Check that no components for inactive elements are defined:
		for this_ion in self.components.keys():
			lines_for_this_ion = list()
			for region in self.regions:
				for line in region.lines:
					if line.ion == this_ion:
						lines_for_this_ion.append(line.active)

			if np.any(lines_for_this_ion):
				pass
			else:
				print "\n [WARNING] - Components defined for inactive element: %s\n" % this_ion


		if self.ready2fit:
			if verbose:
				print "\n  Dataset is ready to be fitted."
				print ""
			return True

	
	def fit(self, verbose=True):
		"""
		Fit the absorption lines using chi-square minimization.
		Returns the best fitting parameters for each component
		of each line.
		"""

		if not self.ready2fit:
		    print " [Error]  - Dataset is not ready to be fit."
		    print "            Run '.prepare_dataset()' before fitting."
		    return False
		
		nsamp = options['nsamp']
		npad = options['npad']

		def chi(pars):
			model = []
			data  = []
			error = []

			for region in self.regions:
				if region.has_active_lines():
					x, y, err, mask = region.unpack()
					res = region.res

					### Generate line profile
					profile_obs = evaluate_profile(x, pars, self.redshift,
												   region.lines, self.components,
												   res, npad, nsamp)

					model.append(profile_obs[mask])
					data.append(np.array(y[mask], dtype=myfloat))
					error.append(np.array(err[mask], dtype=myfloat))
			
			model_spectrum = np.concatenate(model)
			data_spectrum  = np.concatenate(data)
			error_spectrum  = np.concatenate(error)
			
			residual = data_spectrum - model_spectrum
			return residual/error_spectrum
			

		#popt = minimize(chi, self.pars, ftol=1.49e-10)
		popt = minimize(chi, self.pars, ftol=0.01)
		self.best_fit = popt.params
		#popt = minimize(chi, self.pars, maxfev=5000, ftol=1.49012e-10,
		#				factor=1, method='nelder')

		if verbose:
			output.print_results(self, self.best_fit, velocity=False)

		chi2 = popt.chisqr
		return popt, chi2


	def plot_fit(self, active_only=True, linestyles=['--',':'], colors=['b','r']):
		output.plot_fit(self, self.best_fit, active_only, linestyles, colors)
		plt.show()

	def plot_line(self, line_tag, plot_fit=True, linestyles=[':'], colors=['b']):
		output.plot_line(self, line_tag, plot_fit, linestyles, colors)

	def print_results(self, velocity=True, elements='all', systemic=0):
		output.print_results(self, self.best_fit, elements, velocity, systemic)

	def print_metallicity(self, logNHI, err=0.1):
		output.print_metallicity(self, self.best_fit, logNHI, err)

	def print_abundance(self):
		output.print_abundance(self)

	def conf_interval(self, nsim=10):
		import sys

		def chi(pars):
			model = []
			data  = []
			error = []

			for region in self.regions:
				x, y, err, mask = region.unpack()
				### randomize the data within the errors:
				#y += err*np.random.normal(0, 1, size=len(y))

				### Generate line profile
				profile_obs = evaluate_profile(x, pars, self.redshift,
											   region.lines, self.components,
											   res, npad, nsamp)

				model.append(profile_obs[mask])
				data.append(np.array(y[mask], dtype=myfloat))
				error.append(np.array(err[mask], dtype=myfloat))
			
			model_spectrum = np.concatenate(model)
			data_spectrum  = np.concatenate(data)
			error_spectrum  = np.concatenate(error)
			
			residual = data_spectrum - model_spectrum
			return residual/error_spectrum
			

		allPars = {}
		for param in self.pars.keys():
			allPars[param] = []

		allChi = []
		print "\n  Error Estimation in Progress:"
		print ""
		pars_original = self.pars.copy()

		for sim in range(nsim):
			for key in self.pars.keys():
				if key.find('z')==0:
					self.pars[key].value = pars_original[key].value + 0.5e-5*np.random.normal(0,1)

				#elif key.find('logN')==0:
				#	self.pars[key].value = pars_original[key].value + 0.01*np.random.normal(0,1)

				else:
					self.pars[key].value = pars_original[key].value + 0.2*np.random.normal(0,1)

			popt = minimize(chi, self.pars, maxfev=50000, ftol=1.49012e-11, factor=1)
			
			if popt.success:
				for param in popt.params.keys():
					allPars[param].append(popt.params[param].value)

				allChi.append(popt.chisqr)

			sys.stdout.write("\r%6.2f%%" %(100.*(sim+1)/nsim))
			sys.stdout.flush()

		print ""

		return allPars, allChi


def main():
	parser = ArgumentParser()
	parser.add_argument("input", type=str,
			help="VoigtFit input parameter file.")

	args = parser.parse_args()
	parfile = args.input
	parameters = parse_parameters(parfile)

	# Define dataset:
	name = parameters['name']
	if os.path.exists(name+'.dataset'):
		dataset = LoadDataSet(name+'.dataset')

		# Add new lines that were not defined before:
		new_lines = list()
		for tag, velspan in parameters['lines']:
			if tag not in dataset.all_lines:
				new_lines.append([tag, velspan])

		for tag, velspan in new_lines:
				dataset.add_line(tag, velspan)

		# Remove old lines which should not be fitted:
		defined_tags = [tag for (tag, velspan) in parameters['lines']]
		for tag in dataset.all_lines:
			if tag not in defined_tags:
				dataset.deactivate_line(tag)

		# Define Components:
		dataset.reset_components()
		for component in parameters['components']:
			ion, z, b, logN, var_z, var_b, var_N, tie_z, tie_b = component
			dataset.add_component(ion, z, b, logN, var_z=var_z, var_b=var_b, var_N=var_N,
								  tie_z=tie_z, tie_b=tie_b)

		for component in parameters['components_to_copy']:
			ion, anchor, logN, ref_comp, tie_z, tie_b = component
			dataset.copy_components(ion, anchor, logN=logN, ref_comp=ref_comp,
								  tie_z=tie_z, tie_b=tie_b)

		for component in parameters['components_to_delete']:
			dataset.delete_component(*component)

	else:
		dataset = DataSet(parameters['z_sys'])

		# Setup data:
		for fname, res, norm, airORvac in parameters['data']:
			if fname[-5:]=='.fits':
				spec = pf.getdata(fname)
				hdr = pf.getheader(fname)
				wl = hdr['CRVAL1'] + np.arange(len(spec))*hdr['CD1_1']
				N = len(spec)
				err = np.std(spec[N/2-N/20:N/2+N/20])*np.ones_like(spec)

			else:
				data = np.loadtxt(fname)
				if data.shape[1]==2:
					wl, spec = data.T
					N = len(spec)
					err = np.std(spec[N/2-N/20:N/2+N/20])*np.ones_like(spec)
				elif data.shape[1]==3:
					wl, spec, err = data.T
				elif data.shape[1]==4:
					wl, spec, err, mask = data.T

			if airORvac == 'air':
				wl = air2vac(wl)

			dataset.add_data(wl, spec, res, err=err, normalized=norm)

		# Define normalization method:
		#dataset.norm_method = 1
		
		# Toggle nomask:
		#dataset.interactive_mask = True

		# Define lines:
		for tag, velspan in parameters['lines']:
			dataset.add_line(tag, velspan)

		# Define Components:
		dataset.reset_components()
		for component in parameters['components']:
			ion, z, b, logN, var_z, var_b, var_N, tie_z, tie_b = component
			dataset.add_component(ion, z, b, logN, var_z=var_z, var_b=var_b, var_N=var_N,
								  tie_z=tie_z, tie_b=tie_b)

		for component in parameters['components_to_copy']:
			ion, anchor, logN, ref_comp, tie_z, tie_b = component
			dataset.copy_components(ion, anchor, logN=logN, ref_comp=ref_comp,
								  tie_z=tie_z, tie_b=tie_b)

		for component in parameters['components_to_delete']:
			dataset.delete_component(*component)

	# prepare_dataset
	dataset.prepare_dataset()

	# fit
	dataset.fit()

	# print
	dataset.print_results()
	logNHI = parameters['logNHI']
	if logNHI:
		dataset.print_metallicity(*logNHI)

	# plot
	dataset.plot_fit()

	# save
	SaveDataSet(name+'.dataset', dataset)


if __name__=='__main__':
	main()
