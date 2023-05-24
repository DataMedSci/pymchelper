# Simulator mocks

This directory contains mocks for the simulator. They are used to test the simulator without having real binaries
(which requires license, hence we cannot commit them to this repo).

### Generating rfluka mock

To generate the **rfluka** mock, run the following command:

```bash
python3 ./generate_rfluka_mock.py "$FLUKA_EXECUTABLE_PATH/rfluka" ./fluka_minimal/minimal.inp ./fluka_minimal/rfluka
```


### Generating shieldhit mock

To generate the **shieldhit** mock, run the following command:

```bash
python3 ./generate_shieldhit_mock.py "$SHIELDHIT_EXECUTABLE_PATH/shieldhit" ./shieldhit_minimal ./shieldhit_minimal/shieldhit
```


### Generating topas mock

To generate the **topas** mock, run the following command:

```bash
python3 ./generate_topas_mock.py "$TOPAS_EXECUTABLE_PATH/topas" ./topas_minimal/minimal.txt ./topas_minimal/topas
```
