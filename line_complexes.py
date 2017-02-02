import numpy as np

# module to define line-complexes which should be defined simulatneously

fine_structure_complexes = dict()

# - CI 1656 complex
fine_structure_complexes['CI_1656'] = ['CIa_1656',
                                       'CI_1656',
                                       'CIb_1657',
                                       'CIa_1657',
                                       'CIa_1657.9',
                                       'CIb_1658']

# - CI 1560 complex
fine_structure_complexes['CI_1560'] = ['CI_1560',
                                       'CIa_1560',
                                       'CIa_1560.7',
                                       'CIb_1561',
                                       'CIb_1561.4']

# - CI 1328 complex
fine_structure_complexes['CI_1328'] = ['CI_1328',
                                       'CIa_1329',
                                       'CIa_1329.1',
                                       'CIa_1329.12',
                                       'CIb_1329',
                                       'CIb_1329.6']

# - CI 1276 blend
fine_structure_complexes['CI_1276'] = ['CI_1276',
                                       'CIa_1276',
                                       'CI_1277',
                                       'CIa_1277',
                                       'CIa_1277.5',
                                       'CIb_1277',
                                       'CIb_1277.7',
                                       'CIb_1279',
                                       'CIa_1279',
                                       'CI_1280',
                                       'CIb_1280',
                                       'CIa_1280',
                                       'CIa_1280.5',
                                       'CIb_1280.8']

fine_structure_complexes['CI_1277'] = fine_structure_complexes['CI_1276']
fine_structure_complexes['CI_1280'] = fine_structure_complexes['CI_1276']


# ---

CO = [
    # Nu=0:
    [['COJ0_1544.44'],  # J=0
     ['COJ1_1544.54', 'COJ1_1544.38'],  # J=1
     ['COJ2_1544.72', 'COJ2_1544.57', 'COJ2_1544.34'],  # J=2
     ['COJ3_1544.84', 'COJ3_1544.61', 'COJ3_1544.31'],  # J=3
     ['COJ4_1544.98', 'COJ4_1544.68', 'COJ4_1544.30'],  # J=4
     ['COJ5_1545.14', 'COJ5_1544.76', 'COJ5_1544.31']],   # J=5
    # Nu=1:
    [['COJ0_1509.74'],
     ['COJ1_1509.83', 'COJ1_1509.69'],
     ['COJ2_1510.01', 'COJ2_1509.87', 'COJ2_1509.66'],
     ['COJ3_1510.13', 'COJ3_1509.92', 'COJ3_1509.64'],
     ['COJ4_1510.27', 'COJ4_1509.99', 'COJ4_1509.64']],
    # Nu=2:
    [['COJ0_1477.56'],
     ['COJ1_1477.64', 'COJ1_1477.51'],
     ['COJ2_1477.81', 'COJ2_1477.68', 'COJ2_1477.47'],
     ['COJ3_1477.93', 'COJ3_1477.72', 'COJ3_1477.45'],
     ['COJ4_1478.06', 'COJ4_1477.79', 'COJ4_1477.45']],
    # Nu=3:
    [['COJ0_1447.35'],
     ['COJ1_1447.43', 'COJ1_1447.30'],
     ['COJ2_1447.59', 'COJ2_1447.46', 'COJ2_1447.27'],
     ['COJ3_1447.70', 'COJ3_1447.51', 'COJ3_1447.25'],
     ['COJ4_1447.83', 'COJ4_1447.58', 'COJ4_1447.25']],
    # Nu=4:
    [['COJ0_1419.04'],
     ['COJ1_1419.12', 'COJ1_1419.00'],
     ['COJ2_1419.27', 'COJ2_1419.15', 'COJ2_1418.97'],
     ['COJ3_1419.38', 'COJ3_1419.20', 'COJ3_1418.96'],
     ['COJ4_1419.51', 'COJ4_1419.27', 'COJ4_1418.97']],
    # Nu=5:
    [['COJ0_1392.52'],
     ['COJ1_1392.60', 'COJ1_1392.48'],
     ['COJ2_1392.74', 'COJ2_1392.63', 'COJ2_1392.46'],
     ['COJ3_1392.85', 'COJ3_1392.68', 'COJ3_1392.45'],
     ['COJ4_1392.98', 'COJ4_1392.75', 'COJ4_1392.46']],
    # Nu=6:
    [['COJ0_1367.62'],
     ['COJ1_1367.69', 'COJ1_1367.58'],
     ['COJ2_1367.83', 'COJ2_1367.73', 'COJ2_1367.56'],
     ['COJ3_1367.94', 'COJ3_1367.78', 'COJ3_1367.56'],
     ['COJ4_1368.07', 'COJ4_1367.85', 'COJ4_1367.58'],
     ['COJ5_1368.21', 'COJ5_1367.94', 'COJ5_1367.61']],
    # Nu=7:
    [['COJ0_1344.18'],
     ['COJ1_1344.25', 'COJ1_1344.15'],
     ['COJ2_1344.39', 'COJ2_1344.29', 'COJ2_1344.13'],
     ['COJ3_1344.49', 'COJ3_1344.34', 'COJ3_1344.13'],
     ['COJ4_1344.62', 'COJ4_1344.41', 'COJ4_1344.15'],
     ['COJ5_1344.76', 'COJ5_1344.49', 'COJ5_1344.18']],
    # Nu=8:
    [['COJ0_1322.15'],
     ['COJ1_1322.21', 'COJ1_1322.11'],
     ['COJ2_1322.35', 'COJ2_1322.25', 'COJ2_1322.10'],
     ['COJ3_1322.45', 'COJ3_1322.30', 'COJ3_1322.10'],
     ['COJ4_1322.57', 'COJ4_1322.37', 'COJ4_1322.13'],
     ['COJ5_1322.71', 'COJ5_1322.46', 'COJ5_1322.17']],
    # Nu=9:
    [['COJ0_1301.40'],
     ['COJ1_1301.46', 'COJ1_1301.37'],
     ['COJ2_1301.59', 'COJ2_1301.50', 'COJ2_1301.36'],
     ['COJ3_1301.70', 'COJ3_1301.55', 'COJ3_1301.37'],
     ['COJ4_1301.82', 'COJ4_1301.63', 'COJ4_1301.39'],
     ['COJ5_1301.95', 'COJ5_1301.72', 'COJ5_1301.43']],
    # Nu=10:
    [['COJ0_1281.86'],
     ['COJ1_1281.92', 'COJ1_1281.83'],
     ['COJ2_1282.05', 'COJ2_1281.96', 'COJ2_1281.83'],
     ['COJ3_1282.15', 'COJ3_1282.02', 'COJ3_1281.84'],
     ['COJ4_1282.27', 'COJ4_1282.09', 'COJ4_1281.84'],
     ['COJ5_1282.40', 'COJ5_1282.18', 'COJ5_1281.91']],
    # Nu=11:
    [['COJ0_1263.43'],
     ['COJ1_1263.49', 'COJ1_1263.40'],
     ['COJ2_1263.61', 'COJ2_1263.53', 'COJ2_1263.40'],
     ['COJ3_1263.71', 'COJ3_1263.58', 'COJ3_1263.41'],
     ['COJ4_1263.83', 'COJ4_1263.66', 'COJ4_1263.44'],
     ['COJ5_1263.96', 'COJ5_1263.75', 'COJ5_1263.49']]
]

# --- Rotatinal Constants in units of cm^-1
#     E = hc * B * J(J + 1)
rotational_constant = {'H2': 60.853,
                       'CO': 1.9313,
                       'HD': 45.655}

hc = 1.2398e-4         # eV.cm
k_B = 8.6173e-5        # eV/K


def population_of_level(element, T, J):
    """
    Calculate the population of the Jth level relative to the J=0 level.
    The distribution is assumed to be an isothermal Boltzmann distribution:

    n(J) \propto g(J) e^(-E(J) / kT)
    """
    if element not in rotational_constant.keys():
        print " Element is not in database! "
        print " All elements in database are: " + ", ".join(rotational_constant.keys())
        return -1
    else:
        # convert rotational constant to units of Kelvin:
        B = rotational_constant[element]
        B = B * hc / k_B
        n_J = (2*J + 1) * np.exp(-B*J*(J+1)/T)
        return n_J