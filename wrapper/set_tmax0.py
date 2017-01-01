__author__ = 'nyder'


def set_tmax0(value, file_path):
    input_handle = open(file_path, 'r')
    lines = input_handle.readlines()
    input_handle.close()

    for id, line in enumerate(lines):
        if line.startswith("TMAX0"):
            new_line = "TMAX0 " + str(value) + " 0.0     ! Incident energy; (MeV/nucl) \n"
            lines[id] = new_line

    output_handle = open(file_path, 'w')
    output_handle.writelines(lines)
    output_handle.close()

