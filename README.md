# KiCad Auto Silkscreen Placer

**Compatibility:** KiCad v8 & v9

## Overview

This KiCad plugin automatically computes optimal positions for silkscreen reference designators and values, ensuring they do not overlap with other PCB elements such as footprints, solder masks, vias, and holes. The positions are determined using either a **simulated annealing method** or **brute force**, which iteratively adjusts positions to minimize overlap.

The tool is most useful after you’ve laid out and routed your board. It will automate the placement of reference designators and values, saving time compared to manual placement. Some fine-tuning may still be necessary.

## Usage
This is python library and command line tool:

```bash
kicad_auto_silkscreen --method anneal --board test.kicad_pcb --out out-annealed.kicad_pcb --step-size 0.1 --maxiter 100 --max-allowed-distance 10
```


## Performance

The speed of the plugin is primarily affected by the time it takes to compute object collisions. For example, out of a total processing time of 855.025 seconds, the built-in collision calculation takes 542 seconds.


## References

- Originally forked from: [coffeenmusic/Silkscreen_Auto_Placer](https://github.com/coffeenmusic/Silkscreen_Auto_Placer)



