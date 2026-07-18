# Synthetic fixtures

Every file in this directory is invented for testing. It is not an export from TMCO
Consulting, Microsoft Intune, Apple, or any customer environment.

`managed-devices.raw.json` intentionally contains obvious sensitive-looking values so the
sanitizer can prove that it transforms them. The marker text in that file is prohibited from
the generated site. `unknown-field.raw.json` proves that an unclassified provider field stops
publication.
