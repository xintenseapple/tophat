<h1>Tophat</h1>
Tophat is a structured manager for Hack-My-Hat challenges, AKA 'hats'. It
supports encapsulation of hats via Docker containers and provides a robust and
extensible API to expose device functionality to each hat. The goal of this is
to limit the scope of any one challenge to the container it is in plus any
devices exposed through the API.

<h2> Code Structure </h2>
The code for Tophat is divided into four primary pieces:

- Python API: Located in `src/tophat/api`
- Python Device Implementations: Located in `src/tophat/devices`
- Python Hat Implementations: Located in submodule at `src/tophat/hats`
- C Includes: Located in `/include/tophat`

<h3> Python API </h3>
TODO

<h3> Python Device Implementations </h3>
TODO

<h3> Python Hat Implementations </h3>
TODO

<h3> C Includes </h3>
Collection of C header files to help C/C++ code access API functionality.
Contains headers for most devices including helper methods to create and send
their Python API commands.