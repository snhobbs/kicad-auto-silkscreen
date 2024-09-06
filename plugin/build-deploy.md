## Deploying
The workflows are currently not working so here's the manual method:

+ Bump the version to match the tag:
```python
bumpversion --current-version 1.7 patch plugin/pcm/metadata_template.json
```
+ Make the tag
+ Run the build script
```sh
python3 pcm/build.py
```
+ This puts our new PCM compatible zip in /build which we can add as an asset to the release
+ Upload the zip
+ The package validity can be checked with (git@gitlab.com:kicad/addons/metadata.git)
+ The various integrity stats should be integrated with their CI tools

Follow these instructions: https://gitlab.com/kicad/addons/metadata
