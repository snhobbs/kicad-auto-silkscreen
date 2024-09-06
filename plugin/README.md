# Using GUI Locally
For this version the environment variable WXSUPPRESS_SIZER_FLAGS_CHECK=1 needs to be set

```sh
python3 plugin/src/autosilkscreen_plugin.py ${PROJECT}.kicad_pcb
```


# Using CLI
The CLI should be installed as a executable file in the users path when using pip install.

```sh
kicad_auto_silkscreen --board ${PROJECT}.kicad_pcb --out ${OUTPUT}.kicad_pcb
```
