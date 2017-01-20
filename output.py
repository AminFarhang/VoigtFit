import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf
from scipy.signal import fftconvolve, gaussian
import numpy as np
import itertools

import voigt
import Asplund
import spex


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


# ===================================================================================
#
#   Graphics output functions:
# ------------------------------

def plot_fit(dataset, params, active_only=True, linestyles=[':'], colors=['b']):
    """
    Plot best fit absorption profiles.

      INPUT:
    dataset:  VoigtFit.DataSet instance containing the line regions
    params: Output parameter dictionary from VoigtFit.DataSet.fit()

    linestyles:  a list of linestyles to show velocity components
    colors:      a lost of colors to show the velocity components

    The colors and linestyles are combined to form an `iterator'
    which cycles through a set of (linestyle, color).
    """

    plt.close('all')
    for region in dataset.regions:
        if (active_only and region.has_active_lines()) or (not active_only):
            x, y, err, mask = region.unpack()
            cont_err = region.cont_err
            res = region.res

            plt.figure()
            pxs = 0.1
            wl_line = np.arange(x.min(), x.max(), pxs)
            ref_line = region.lines[-1]
            l0, f, gam = ref_line.get_properties()
            l_ref = l0*(dataset.redshift + 1)
            npad = 20
            nsamp = 1

            front_padding = np.linspace(wl_line.min()-npad*pxs, wl_line.min(), npad, endpoint=False)
            end_padding = np.linspace(wl_line.max()+pxs, wl_line.max()+npad*pxs, npad)
            wl_line = np.concatenate([front_padding, wl_line, end_padding])
            tau = np.zeros_like(wl_line)

            for line in region.lines:
                if (active_only and line.active) or (not active_only):
                    # Reset line properties for each element
                    component_prop = itertools.product(linestyles, colors)
                    component_prop = itertools.cycle(component_prop)

                    # Load line properties
                    l0, f, gam = line.get_properties()
                    ion = line.ion
                    if ion in dataset.components.keys():
                        n_comp = len(dataset.components[ion])

                        ion = ion.replace('*','x')
                        for n in range(n_comp):
                            z = params['z%i_%s'%(n, ion)].value
                            b = params['b%i_%s'%(n, ion)].value
                            logN = params['logN%i_%s'%(n, ion)].value
                            tau += voigt.Voigt(wl_line, l0, f, 10**logN, 1.e5*b, gam, z=z)

                            ls, color = component_prop.next()
                            plt.axvline((l0*(z+1)-l_ref)/l_ref*299792., ls=ls, color=color)

            profile_int = np.exp(-tau)
            fwhm_instrumental = res/299792.*l_ref
            sigma_instrumental = fwhm_instrumental/2.35482/pxs
            LSF = gaussian(len(wl_line), sigma_instrumental)
            LSF = LSF/LSF.sum()
            profile_broad = fftconvolve(profile_int, LSF, 'same')
            profile = profile_broad[npad:-npad]
            wl_line = wl_line[npad:-npad]
            vel_profile = (wl_line-l_ref)/l_ref*299792.

            plt.ylim(profile.min()-0.1, 1.15)
            plt.xlim(-region.velocity_span, region.velocity_span)

            vel  = (x-l_ref)/l_ref*299792.

            # Expand mask by 1 pixel around each masked range
            # to draw the lines correctly
            mask_idx = np.where(mask==0)[0]
            big_mask_idx = np.union1d(mask_idx+1, mask_idx-1)
            big_mask = np.ones_like(mask, dtype=bool)
            big_mask[big_mask_idx]=False
            masked_range = np.ma.masked_where(big_mask, y)
            plt.plot(vel, masked_range, color='0.7', drawstyle='steps-mid', lw=0.9)

            spectrum = np.ma.masked_where(~mask, y)
            error = np.ma.masked_where(~mask, err)
            plt.errorbar(vel, spectrum, err, ls='', color='gray')
            plt.plot(vel, spectrum, color='k', drawstyle='steps-mid')

            plt.plot(vel_profile, profile, color='r', lw=1.5)

            plt.xlabel("Velocity  [${\\rm km\,s^{-1}}$]")
            plt.ylabel("Normalized flux")
            plt.axhline(1., ls='--', color='k')
            plt.axhline(1.+cont_err, ls=':', color='gray')
            plt.axhline(1.-cont_err, ls=':', color='gray')

            title_string = ", ".join([line.tag for line in region.lines])
            plt.title(title_string)


# The function plot_line is deprecated, use plot_single_line!
# def plot_line(dataset, line_tag, plot_fit=True, linestyles=[':'], colors=['b'], subsample_profile=1):
#     """
#     Plot absorption line.
#
#       INPUT:
#     dataset:  VoigtFit.DataSet instance containing the line regions
#     line_tag: The line tag of the line to show, e.g., 'FeII_2374'
#
#     plot_fit:    if True, the best-fit profile will be shown
#     linestyles:  a list of linestyles to show velocity components
#     colors:      a lost of colors to show the velocity components
#
#     The colors and linestyles are combined to form an `iterator'
#     which cycles through a set of (linestyle, color).
#     """
#
#     if line_tag not in dataset.all_lines:
#         plt.figure()
#         dataset.add_line(line_tag, active=False)
#         dataset.prepare_dataset()
#
#     region = dataset.find_line(line_tag)
#
#     x, y, err, mask = region.unpack()
#     cont_err = region.cont_err
#     res = region.res
#
#     ref_line = region.lines[-1]
#     l0, f, gam = ref_line.get_properties()
#     l_ref = l0*(dataset.redshift + 1)
#
#     plt.figure(figsize=(6,3.75))
#     plt.subplots_adjust(bottom=0.15, right=0.98)
#
#     if plot_fit and isinstance(dataset.best_fit, dict):
#         if subsample_profile:
#             N_pix = len(x)*subsample_profile
#             wl_line = np.linspace(x.min(), x.max(), N_pix)
#         else:
#             wl_line = x
#
#         ref_line = region.lines[-1]
#         l0, f, gam = ref_line.get_properties()
#         l_ref = l0*(dataset.redshift + 1)
#         npad = 20
#         nsamp = 1
#
#         front_padding = np.linspace(wl_line.min()-npad*pxs, wl_line.min(), npad, endpoint=False)
#         end_padding = np.linspace(wl_line.max()+pxs, wl_line.max()+npad*pxs, npad)
#         wl_line = np.concatenate([front_padding, wl_line, end_padding])
#         tau = np.zeros_like(wl_line)
#
#         params = dataset.best_fit
#         for line in region.lines:
#             # Reset line properties for each element
#             component_prop = itertools.product(linestyles, colors)
#             component_prop = itertools.cycle(component_prop)
#
#             # Load line properties
#             l0, f, gam = line.get_properties()
#             ion = line.ion
#             n_comp = len(dataset.components[ion])
#
#             ion = ion.replace('*','x')
#             for n in range(n_comp):
#                 z = params['z%i_%s'%(n, ion)].value
#                 b = params['b%i_%s'%(n, ion)].value
#                 logN = params['logN%i_%s'%(n, ion)].value
#                 tau += voigt.Voigt(wl_line, l0, f, 10**logN, 1.e5*b, gam, z=z)
#
#                 ls, color = component_prop.next()
#                 plt.axvline((l0*(z+1)-l_ref)/l_ref*299792., ls=ls, color=color)
#
#         profile_int = np.exp(-tau)
#         fwhm_instrumental = res/299792.*l_ref
#         sigma_instrumental = fwhm_instrumental/2.35482/pxs
#         LSF = gaussian(len(wl_line), sigma_instrumental)
#         LSF = LSF/LSF.sum()
#         profile_broad = fftconvolve(profile_int, LSF, 'same')
#         profile = profile_broad[npad:-npad]
#         wl_line = wl_line[npad:-npad]
#         vel_profile = (wl_line-l_ref)/l_ref*299792.
#
#     plt.ylim(y[mask].min()-0.1)
#     plt.xlim(-region.velocity_span, region.velocity_span)
#
#     vel  = (x-l_ref)/l_ref*299792.
#
#     # Expand mask by 1 pixel around each masked range
#     # to draw the lines correctly
#     mask_idx = np.where(mask==0)[0]
#     big_mask_idx = np.union1d(mask_idx+1, mask_idx-1)
#     big_mask = np.ones_like(mask, dtype=bool)
#     big_mask[big_mask_idx]=False
#     masked_range = np.ma.masked_where(big_mask, y)
#     plt.plot(vel, masked_range, color='0.7', drawstyle='steps-mid', lw=0.9)
#
#     spectrum = np.ma.masked_where(~mask, y)
#     error = np.ma.masked_where(~mask, err)
#     plt.errorbar(vel, spectrum, err, ls='', color='gray')
#     plt.plot(vel, spectrum, color='k', drawstyle='steps-mid')
#     plt.axhline(0., ls='--', color='0.7', lw=0.7)
#
#     if plot_fit:
#         plt.plot(vel_profile, profile, color='r', lw=1.5)
#         plt.ylim(profile.min()-0.1, 1.15)
#
#     plt.xlabel("Velocity  [${\\rm km\,s^{-1}}$]")
#     plt.ylabel("Normalized flux")
#     plt.axhline(1., ls='--', color='k')
#     plt.axhline(1. + cont_err, ls=':', color='gray')
#     plt.axhline(1. - cont_err, ls=':', color='gray')
#
#     title_string = ", ".join([line.tag for line in region.lines])
#     plt.title(title_string)
#     plt.show()

# A4 figuse size:
# fig = plt.figure(figsize=(7, 9.899))


def plot_all_lines(dataset, plot_fit=False, linestyles=['--'], colors=['b'],
                   rebin=1, fontsize=12, xmin=None, xmax=None, max_rows=5,
                   filename=None, show=True, subsample_profile=1, npad=50):
    """
    Plot absorption line.

      INPUT:
    dataset:  VoigtFit.DataSet instance containing the line regions
    line_tag: The line tag of the line to show, e.g., 'FeII_2374'

    plot_fit:    if True, the best-fit profile will be shown
    linestyles:  a list of linestyles to show velocity components
    colors:      a lost of colors to show the velocity components

    The colors and linestyles are combined to form an `iterator'
    which cycles through a set of (linestyle, color).

    loc: places the line tag (based on the plt.legend keyword *loc*)

    rebin: integer factor for rebinning the spectrum

    nolabels: show axis labels?
    """

    # --- First figure out which lines to plot to avoid overlap
    #     of several lines defined in the same region.
    included_lines = list()
    lines_to_plot = list()
    for ref_line in dataset.lines.values():
        if ref_line.tag in included_lines:
            pass
        elif ref_line.ion[-1].islower():
            # do not plot individual figures for fine-structure lines
            included_lines.append(ref_line)
        else:
            region = dataset.find_line(ref_line.tag)
            lines_to_plot.append(ref_line.tag)
            if len(region.lines) == 1:
                included_lines.append(ref_line.tag)
            else:
                l_ref = ref_line.l0*(dataset.redshift + 1)
                for line in region.lines:
                    l0 = line.l0
                    delta_v = (l0*(dataset.redshift + 1) - l_ref) / l_ref * 299792.
                    if np.abs(delta_v) <= 150 or line.ion[-1].islower() is True:
                        included_lines.append(line.tag)
            l0 = line.l0
            delta_v = (l0*(dataset.redshift + 1) - l_ref) / l_ref * 299792.

    # --- If *filename* is given, set up a PDF container for saving to file:
    if filename:
        if '.pdf' not in filename:
            filename += '.pdf'
        pdf = matplotlib.backends.backend_pdf.PdfPages(filename)

    # --- Determine number of pages to create:
    pages = list(chunks(lines_to_plot, 2*max_rows))
    lines_in_figure = list()
    for contents in pages:
        # --- Determine figure size:
        if len(contents) > 1:
            width = 7
            columns = 2
        else:
            width = 3.5
            columns = 1

        heigth = (len(contents) + 1) / 2 * 9.899/max_rows
        rows = (len(contents) + 1) / 2

        fig = plt.figure(figsize=(width, heigth))
        fig.subplots_adjust(left=0.08, right=0.98, top=0.98)

        num = 1
        for line_tag in contents:
            if line_tag in lines_in_figure:
                pass
            else:
                ax = fig.add_subplot(rows, columns, num)
                _, LIV = plot_single_line(dataset, line_tag,
                                          plot_fit=plot_fit, linestyles=linestyles,
                                          colors=colors, rebin=rebin, nolabels=True, axis=ax,
                                          fontsize=fontsize, xmin=xmin, xmax=xmax, show=show,
                                          subsample_profile=subsample_profile, npad=npad)
                lines_in_figure += LIV
                num += 1
                # LIV is a shorthand for 'lines_in_view'

        if filename:
            pdf.savefig(fig)

    if filename:
        pdf.close()
        print "\n  Output saved to PDF file:  " + filename

    if show:
        plt.show()


def plot_single_line(dataset, line_tag, plot_fit=False, linestyles=['--'], colors=['b'],
                     loc='left', rebin=1, nolabels=False, axis=None, fontsize=12,
                     xmin=None, xmax=None, ymin=None, show=True, subsample_profile=1, npad=50):
    """
    Plot absorption line.

      INPUT:
    dataset:  VoigtFit.DataSet instance containing the line regions
    line_tag: The line tag of the line to show, e.g., 'FeII_2374'

    plot_fit:    if True, the best-fit profile will be shown
    linestyles:  a list of linestyles to show velocity components
    colors:      a lost of colors to show the velocity components

    The colors and linestyles are combined to form an `iterator'
    which cycles through a set of (linestyle, color).

    loc: places the line tag (right or left), default *left*.

    rebin: integer factor for rebinning the spectrum

    nolabels: show axis labels?
    """

    if line_tag not in dataset.all_lines:
        dataset.add_line(line_tag, active=False)
        dataset.prepare_dataset()

    region = dataset.find_line(line_tag)

    x, y, err, mask = region.unpack()
    cont_err = region.cont_err
    res = region.res

    if rebin > 1:
        x, y, err = spex.rebin_spectrum(x, y, err, rebin)
        mask = spex.rebin_bool_array(mask, rebin)

    ref_line = dataset.lines[line_tag]
    l0, f, gam = ref_line.get_properties()
    l_ref = l0*(dataset.redshift + 1)

    # - Check if lines are separated by more than 200 km/s
    #   if so, then remove the line from the view.
    lines_in_view = list()
    for line in region.lines:
        l0 = line.l0
        delta_v = (l0*(dataset.redshift + 1) - l_ref) / l_ref * 299792.
        if np.abs(delta_v) <= 150 or line.ion[-1].islower() is True:
            lines_in_view.append(line.tag)

    if axis:
        ax = axis
    else:
        plt.close('all')
        fig = plt.figure(figsize=(6, 3.5))
        ax = fig.add_subplot(111)
        fig.subplots_adjust(bottom=0.15, right=0.97, top=0.98)

    if plot_fit and (isinstance(dataset.best_fit, dict) or
                     isinstance(dataset.pars, dict)):

        if subsample_profile > 1:
            N_pix = len(x)*subsample_profile
            wl_line = np.logspace(np.log10(x.min()), np.log10(x.max()), N_pix)
        else:
            wl_line = x
        pxs = np.mean(np.diff(wl_line))
        ref_line = dataset.lines[line_tag]
        l0, f, gam = ref_line.get_properties()
        l_ref = l0*(dataset.redshift + 1)

        front_padding = np.linspace(wl_line.min()-npad*pxs, wl_line.min(), npad, endpoint=False)
        end_padding = np.linspace(wl_line.max()+pxs, wl_line.max()+npad*pxs, npad)
        wl_line = np.concatenate([front_padding, wl_line, end_padding])
        tau = np.zeros_like(wl_line)

        if isinstance(dataset.best_fit, dict):
            params = dataset.best_fit
        else:
            params = dataset.pars

        for line in region.lines:
            # Reset line properties for each element
            component_prop = itertools.product(linestyles, colors)
            component_prop = itertools.cycle(component_prop)

            # Load line properties
            l0, f, gam = line.get_properties()
            ion = line.ion
            n_comp = len(dataset.components[ion])

            ion = ion.replace('*', 'x')
            if line.active:
                for n in range(n_comp):
                    z = params['z%i_%s' % (n, ion)].value
                    b = params['b%i_%s' % (n, ion)].value
                    logN = params['logN%i_%s' % (n, ion)].value
                    tau += voigt.Voigt(wl_line, l0, f, 10**logN, 1.e5*b, gam, z=z)

                    ls, color = component_prop.next()
                    ax.axvline((l0*(z+1) - l_ref)/l_ref*299792., ls=ls, color=color)
            else:
                ax.axvline((l0*(z+1) - l_ref)/l_ref*299792., ls=ls, color='0.5')

        profile_int = np.exp(-tau)
        fwhm_instrumental = res/299792.*l_ref
        sigma_instrumental = fwhm_instrumental/2.35482/pxs
        LSF = gaussian(len(wl_line), sigma_instrumental)
        LSF = LSF/LSF.sum()
        profile_broad = fftconvolve(profile_int, LSF, 'same')
        profile = profile_broad[npad:-npad]
        wl_line = wl_line[npad:-npad]
        vel_profile = (wl_line - l_ref)/l_ref*299792.

    vel = (x - l_ref) / l_ref * 299792.

    if not xmin:
        xmin = -region.velocity_span

    if not xmax:
        xmax = region.velocity_span
    ax.set_xlim(xmin, xmax)

    view_part = (vel > xmin) * (vel < xmax)

    if not ymin:
        ymin = y[view_part].min() - 1.5*err.mean()
    ymax = (y*mask)[view_part].max() + 2*err.mean()
    ax.set_ylim(ymin, ymax)

    # Expand mask by 1 pixel around each masked range
    # to draw the lines correctly
    mask_idx = np.where(mask == 0)[0]
    big_mask_idx = np.union1d(mask_idx+1, mask_idx-1)
    big_mask = np.ones_like(mask, dtype=bool)
    big_mask[big_mask_idx] = False
    masked_range = np.ma.masked_where(big_mask, y)
    ax.plot(vel, masked_range, color='0.7', drawstyle='steps-mid', lw=0.9)

    spectrum = np.ma.masked_where(~mask, y)
    # error = np.ma.masked_where(~mask, err)
    ax.errorbar(vel, spectrum, err, ls='', color='gray')
    ax.plot(vel, spectrum, color='k', drawstyle='steps-mid')
    ax.axhline(0., ls='--', color='0.7', lw=0.7)

    if plot_fit and (isinstance(dataset.best_fit, dict) or
                     isinstance(dataset.pars, dict)):
        ax.plot(vel_profile, profile, color='r', lw=1.5)

    if nolabels:
        if axis:
            pass
        else:
            fig.subplots_adjust(bottom=0.07, right=0.98, left=0.08, top=0.98)
    else:
        ax.set_xlabel("${\\rm Velocity}\ \ [{\\rm km\,s^{-1}}]$")
        ax.set_ylabel("${\\rm Normalized\ flux}$")
    ax.axhline(1., ls='--', color='k')
    ax.axhline(1. + cont_err, ls=':', color='gray')
    ax.axhline(1. - cont_err, ls=':', color='gray')

    transition_lines = list()
    for line_tag in lines_in_view:
        ion = line_tag.split('_')[0]
        if ion[-1].islower():
            pass
        else:
            transition_lines.append(line_tag)

    title_string = ", ".join(transition_lines)
    line_string = "${\\rm %s}$" % title_string.replace('_', '\ ')

    if loc == 'right':
        label_x = 0.97
    elif loc == 'left':
        label_x = 0.03
    else:
        label_x = 0.03
        loc = 'left'
    ax.text(label_x, 0.05, line_string, va='bottom', ha=loc,
            transform=ax.transAxes, fontsize=fontsize)

    if show:
        plt.show()

    return (ax, lines_in_view)


# ===================================================================================
#
#   Text output functions:
# --------------------------


def print_results(dataset, params, elements='all', velocity=True, systemic=0):
    """
    Plot best fit absorption profiles.

      INPUT:
    dataset:  VoigtFit.DataSet instance containing the line regions
    params: Output parameter dictionary from VoigtFit.DataSet.fit()

    if velocity is set to 'False' the components redshift is shown instead
    of the velocity relative to the systemic redshift.

    if systemic is set the velocities will be relative to this redshift;
    default behaviour is to use the systemic redshift defined in the dataset.

    """

    if systemic:
        z_sys = systemic
    else:
        z_sys = dataset.redshift

    print "\n  Best fit parameters\n"
    print "\t\t\t\tlog(N)\t\t\tb"
    if elements == 'all':
        for ion in dataset.components.keys():
            lines_for_this_ion = []
            for line_tag, line in dataset.lines.items():
                if line.ion == ion and line.active:
                    lines_for_this_ion.append(line_tag)

            all_transitions = [trans.split('_')[1] for trans in sorted(lines_for_this_ion)]
            # Split list of transitions into chunks of length=4
            # join the transitions in each chunks
            # and join each chunk with 'newline'
            trans_chunks = [", ".join(sublist) for sublist in list(chunks(all_transitions, 4))]
            indent = '\n'+(len(ion)+2)*' '
            trans_string = indent.join(trans_chunks)

            print ion + "  "+trans_string
            n_comp = len(dataset.components[ion])
            for n in range(n_comp):
                ion = ion.replace('*','x')
                z = params['z%i_%s'%(n, ion)].value
                b = params['b%i_%s'%(n, ion)].value
                logN = params['logN%i_%s'%(n, ion)].value
                z_err = params['z%i_%s'%(n, ion)].stderr
                b_err = params['b%i_%s'%(n, ion)].stderr
                logN_err = params['logN%i_%s'%(n, ion)].stderr

                if velocity:
                    z_std = z_err/(z_sys+1)*299792.
                    z_val = (z-z_sys)/(z_sys+1)*299792.
                    z_format = "v = %5.1f +/- %.1f\t"
                else:
                    z_std = z_err
                    z_val = z
                    z_format = "z = %.6f +/- %.6f"

                output_string = z_format%(z_val,z_std)+"\t\t"
                output_string += "%.2f +/- %.2f\t\t"%(logN,logN_err)
                output_string += "%.1f +/- %.1f"%(b,b_err)

                print output_string

            print ""

    else:
        for ion in elements:
            lines_for_this_ion = []
            for line_tag, line in dataset.lines.items():
                if line.ion == ion and line.active:
                    lines_for_this_ion.append(line_tag)

            all_transitions = ", ".join([trans.split('_')[1] for trans in sorted(lines_for_this_ion)])
            print ion + "  "+all_transitions
            n_comp = len(dataset.components[ion])
            for n in range(n_comp):
                ion = ion.replace('*','x')
                z = params['z%i_%s'%(n, ion)].value
                b = params['b%i_%s'%(n, ion)].value
                logN = params['logN%i_%s'%(n, ion)].value
                b_err = params['b%i_%s'%(n, ion)].stderr
                logN_err = params['logN%i_%s'%(n, ion)].stderr

                if velocity:
                    z_val = (z-z_sys)/(z_sys+1)*299792.
                    z_format = "v = %5.1f\t"
                else:
                    z_val = z
                    z_format = "z = %.6f"

                output_string = z_format%(z_val,z_std)+"\t\t"
                output_string += "%.2f +/- %.2f\t\t"%(logN,logN_err)
                output_string += "%.1f +/- %.1f"%(b,b_err)

                print output_string

            print ""


def print_metallicity(dataset, params, logNHI, err=0.1):
    """
    Plot best fit absorption profiles.

      INPUT:
    dataset:  VoigtFit.DataSet instance containing the line regions
    params: Output parameter dictionary from VoigtFit.DataSet.fit()
    logNHI:   Column density of neutral hydrogen
    err:      Uncertainty on logNHI

    """

    print "\n  Metallicities\n"
    print "  log(NHI) = %.2f +/- %.2f\n" % (logNHI, err)
    logNHI = np.random.normal(logNHI, err, 10000)
    for ion in dataset.components.keys():
        element = ion[:2] if ion[1].islower() else ion[0]
        logN = []
        logN_err = []
        N_tot = []
        for par in params.keys():
            if par.find('logN')>=0 and par.find(ion)>=0:
                N_tot.append(params[par].value)
                if params[par].stderr < 0.9:
                    logN.append(params[par].value)
                    if params[par].stderr < 0.01:
                        logN_err.append(0.01)
                    else:
                        logN_err.append(params[par].stderr)

        ION = [np.random.normal(n,e,10000) for n,e in zip(logN, logN_err)]
        l68, abundance, u68 = np.percentile(np.log10(np.sum(10**np.array(ION),0)),[16, 50, 84])
        std_err = np.std(np.log10(np.sum(10**np.array(ION),0)))

        logN_tot = np.random.normal(abundance, std_err, 10000)
        N_solar, N_solar_err = Asplund.photosphere[element]
        solar_abundance = np.random.normal(N_solar, N_solar_err, 10000)

        metal_array = abundance - logNHI - (solar_abundance - 12.)
        metal = np.mean(metal_array)
        metal_err = np.std(metal_array)
        print "  [%s/H] = %.2f +/- %.2f" %(element, metal, metal_err)

def print_abundance(dataset):
    """
    Plot best fit absorption profiles.
    """

    if isinstance(dataset.best_fit, dict):
        params = dataset.best_fit
        print "\n  Total Abundances\n"
        for ion in dataset.components.keys():
            element = ion[:2] if ion[1].islower() else ion[0]
            logN = []
            logN_err = []
            N_tot = []
            for par in params.keys():
                if par.find('logN')>=0 and par.find(ion)>=0:
                    N_tot.append(params[par].value)
                    if params[par].stderr < 0.9:
                        logN.append(params[par].value)
                        if params[par].stderr < 0.01:
                            logN_err.append(0.01)
                        else:
                            logN_err.append(params[par].stderr)

            ION = [np.random.normal(n,e,10000) for n,e in zip(logN, logN_err)]
            l68, abundance, u68 = np.percentile(np.log10(np.sum(10**np.array(ION),0)),[16, 50, 84])
            std_err = np.std(np.log10(np.sum(10**np.array(ION),0)))

            print "  logN(%s) = %.2f +/- %.2f" %(ion, abundance, std_err)

    else:
        print "\n [ERROR] - The dataset has not yet been fitted. No parameters found!"
