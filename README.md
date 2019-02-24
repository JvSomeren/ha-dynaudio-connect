# Home Assistant Dynaudio Connect component
This component has been built based on the [API reference](https://github.com/therealmuffin/dynaudio-connect-api) made by [therealmuffin](https://github.com/therealmuffin/).

## Installation as custom component
Place the [`media_player.py`](dynaudio/media_player.py)-file at the following path `$HOMEASSISTANT_HOME/custom_components/dynaudio/media_player.py`.

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
* Volume up/down

## Licence
This project is licensed under [MIT license](http://opensource.org/licenses/MIT).
For the full text of the license, see the [LICENSE.md](LICENSE.md) file.
