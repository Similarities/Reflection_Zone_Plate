import matplotlib.pyplot as plt
import numpy as np
import Basic_file_app


class CountsToPhotonNumber:
    def __init__(self, data, calibration_electron_per_photon, calibration_q_a):
        self.data = data
        self.sensitivity = 0.83 / 2.5  # counts per electron for low gain
        self.capture_angle = 4.72E-6  # sr for RZP A9
        self.calibration_photon_number, self.quantum_efficiency = \
            self.prepare_calibration_files(calibration_electron_per_photon, calibration_q_a)

        self.result = np.zeros([len(self.data)-1, 2])
        print(len(self.data), 'len data')

    def change_energy(self, photon_energy, counts):
        self.photon_energy = photon_energy
        self.counts = counts
        return self.photon_energy, self.counts

    def prepare_calibration_files(self, electron_calibration_file, quantum_efficiency_calibration_file):
        calibration_energy = Basic_file_app.load_1d_array(electron_calibration_file, 0, 0)
        calibration_electrons_per_photon_energy = Basic_file_app.load_1d_array(electron_calibration_file, 1, 0)
        self.calibration_photon_number = Basic_file_app.stack_arrays(calibration_energy,
                                                                     calibration_electrons_per_photon_energy, axis=1)

        calibration_energy = Basic_file_app.load_1d_array(quantum_efficiency_calibration_file, 0, 0)
        calibration_quantum = Basic_file_app.load_1d_array(quantum_efficiency_calibration_file, 1, 0)
        self.quantum_efficiency = Basic_file_app.stack_arrays(calibration_energy, calibration_quantum, axis=1)

        return self.calibration_photon_number, self.quantum_efficiency

    def number_of_electrons(self, counts):
        return counts / self.sensitivity

    def correct_quantum_efficiency_ccd(self, photon_energy):
        index = np.where(self.quantum_efficiency[::, 0] >= photon_energy)[0][0]
        counts_qe = self.quantum_efficiency[index, 1] / 100
        # print("entry engery in qe", self.quantum_efficiency[index])
        return counts_qe

    def number_of_photons(self, photon_energy, electron_number):
        index = np.where(self.calibration_photon_number[::, 0] >= photon_energy)[0][0]
        counts_cam = self.calibration_photon_number[index, 1]
        q_e = self.correct_quantum_efficiency_ccd(photon_energy)
        # print("calibration ccd for photon energy:", self.calibration_photon_number[index])
        # print("calibration ccd and qe:", counts_cam, q_e)
        return electron_number / (counts_cam * q_e)

    def number_of_photons_per_sr(self, number_of_photons):
        return number_of_photons / self.capture_angle

    def bandwidth_correction(self, energy_1, energy_2):
        delta_energy = energy_2 - energy_1
        #print('bandwith:', delta_energy, "at:", energy_1, '0.1% bandwidth', 0.001 * energy_1)
        correction_constant = (0.001 * energy_1) / delta_energy
        return correction_constant

    def evaluate_data(self):
        print(len(self.data), self.data[-1])
        for counter, value in enumerate(self.data[0:-1, 0]):
            #print(counter, value)
            self.result[counter, 0] = value
            counts = data[counter, 1]
            electrons = self.number_of_electrons(counts)
            photons = self.number_of_photons(value, electrons)
            photons_per_sr = self.number_of_photons_per_sr(photons)
            self.result[counter, 1] = photons_per_sr * self.bandwidth_correction(value, data[counter + 1, 0])
        return self.result

    def evalute_single_data_point(self, selected_energy):
        index = np.where(self.data[::, 0] >= selected_energy)[0][0]
        counts = self.data[index, 1]
        print("xxxxxxxxxxxx", selected_energy)
        print("energy and counts in data", self.data[index])
        electrons = self.number_of_electrons(counts)
        print("electrons:", electrons)
        photons = self.number_of_photons(selected_energy, electrons)
        print('photons:', photons)
        photons_per_sr = self.number_of_photons_per_sr(photons)
        print("photons per sr:", photons_per_sr)
        index_data = np.where(self.data[::, 0] >= selected_energy)[0][0]
        real_unit = photons_per_sr * self.bandwidth_correction(data[index_data, 0], data[index_data + 1, 0])
        print("real unit: ", real_unit)

        return self.data[index, 0], real_unit

    def correct_for_filter_transmission_single_value(self, energy, counts, filter_array):
        index = np.where(filter_array[:,0] >= energy)[0][0]
        print("filter:", filter_array[index])
        filter_corrected = counts/filter_array[index,1]
        return filter_corrected

    def correct_for_filter_transmission_array(self, filter_array):
        for counter, value in enumerate(self.result[:,0]):
            energy = value
            counts = self.result[counter, 1]
            self.result[counter,1] = self.correct_for_filter_transmission_single_value(energy, counts, filter_array)
        return self.result


data_file = "data_intensity/210205_PM040653_calibrated_analytical.txt"
data = Basic_file_app.stack_arrays(Basic_file_app.load_1d_array(data_file, 1, 4),
                                   Basic_file_app.load_1d_array(data_file, 2, 4), axis=1)

data_below_1000ev = data[0:1059]

calibration_number_e_per_photon = "electrons_per_photon_interpolation_bin_size_0.01.txt"
calibration_q_a = "QE_greateyesGE_BI_interpolation_bin_size_0.01.txt"

al_filter_file = "Al_500nm_eV_interpolation_bin_size_0.05.txt"
al_filter = Basic_file_app.stack_arrays(Basic_file_app.load_1d_array(al_filter_file, 0, 0),
                                        Basic_file_app.load_1d_array(al_filter_file,1,0), axis=1)

mylar_filter_file = "Mylar_900nm_eV_interpolation_bin_size_0.05.txt"
mylar_filter = Basic_file_app.stack_arrays(Basic_file_app.load_1d_array(mylar_filter_file, 0, 0),
                                        Basic_file_app.load_1d_array(mylar_filter_file,1,0), axis=1)

Test = CountsToPhotonNumber(data_below_1000ev, calibration_number_e_per_photon, calibration_q_a)
Test.evaluate_data()
Test.correct_for_filter_transmission_array(al_filter)
aha = Test.correct_for_filter_transmission_array(mylar_filter)

plt.plot(aha[:,0], aha[:,1])
plt.show()







# ToDo: sort by initial energy (or by value) then: calc with sensitivity for value calibration value
# ToDo: implement filter - do the same with filter
# ToDo: implement capture angle / per s for measurement
# ToDo: join it.
