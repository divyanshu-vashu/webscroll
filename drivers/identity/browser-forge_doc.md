BrowserforgeFingerprintGenerator
FingerprintGenerator adapter for fingerprint generator from browserforge.

browserforge is a browser header and fingerprint generator: https://github.com/daijro/browserforge

Hierarchy
FingerprintGenerator
BrowserforgeFingerprintGenerator
Index 
Methods
__init__
generate
Methods 
__init__
 __init__(*, header_options, screen_options, mock_web_rtc, slim): None
Initialize a new instance.

All generator options are optional. If any value is not specified, then None is set in the options. Default values for options set to None are implementation detail of used fingerprint generator. Specific default values should not be relied upon. Use explicit values if it matters for your use case.

Parameters
header_options: HeaderGeneratorOptions | None = None
Collection of header related attributes that can be used by the fingerprint generator.

screen_options: ScreenOptions | None = None
Defines the screen constrains for the fingerprint generator.

mock_web_rtc: bool | None = None
Whether to mock WebRTC when injecting the fingerprint.

slim: bool | None = None
Disables performance-heavy evasions when injecting the fingerprint.

Returns None
generate
 generate(): Fingerprint
Overrides FingerprintGenerator.generate

Generate browser fingerprints.

This is experimental feature. Return type is temporarily set to Fingerprint from browserforge. This is subject to change and most likely it will change to custom Fingerprint class defined in this repo later.

Returns Fingerprint