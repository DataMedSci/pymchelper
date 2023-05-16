# Simulator mocks

This directory contains mocks for the simulator. They are used to test the simulator without having real fluka binaries.

### Generating rfluka mock

To generate the **rfluka** mock, run the following command:

```bash
python3 ./generate_rfluka_mock.py "$FLUKA_EXECUTABLE_PATH/rfluka" ./fluka_input/minimal.inp ./bin/rfluka
```
