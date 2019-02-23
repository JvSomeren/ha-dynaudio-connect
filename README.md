# Home Assistant Dynaudio Connect component
This component has been built based on the [API reference](https://github.com/therealmuffin/dynaudio-connect-api) made by [therealmuffin](https://github.com/therealmuffin/).

## Installation as custom component
Place the [`dynaudio.py`](dynaudio.py)-file at the following path `$HOMEASSISTANT_HOME/custom_components/media_player/dynaudio.py`.

Inside your `configurations.yaml` add the following code:

```
media_player:
  - platform: dynaudio
    host: $ip-address
    port: $port (optional)
    name: $custom-name (optional)
```

## TODO
* Expand update function to reflect device state

## Licence
This project is licensed under [MIT license](http://opensource.org/licenses/MIT).
For the full text of the license, see the [LICENSE.md](LICENSE.md) file.
