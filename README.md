# Scale model telescope tracker
## Background
I live near a large, old radiotelescope (26m / 85' diameter from the NASA tracking era) that's still being used for radioastronomy and space tracking. I figured it'd be nice to have a scale model in my office that mirrored the movements of the real thing using the web feeds of the dish status.

## Vague plan
* Obtain drawings or lots of photographs to build replica model.
* Build cardboard mockup of the X (lower)/ Y (upper) motors / tracking arc

* 3d print? (requires digital model) or fabricate model from drawings (I may be down the local men's shed a LOT for this)

* Write control software for (likely) pair of stepper motors for X/Y movement that matches a given position.
* Given steppers have no indication of where they are at power up, either build a homing routine with limit switches, and/or put a 3 axis accelerometer in the focus box (hey, the real thing has feedlines / cryo pipes from ground up to there)

* Inevitable scope creep - Make the aero lights indicate current mode - stowed, tracking, fast slew etc. Add warning LEDs on the ground building for (real) safety / watchdog / limit / panic status.

* landscape it all prettily so try and stick to a scale I can get "dressing" kit from a model shop like containers, trees, people

* Artistic licence and add a windsock (there isn't one on site) with an LED when wind_state != WIND_OK


