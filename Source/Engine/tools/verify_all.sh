#!/usr/bin/env bash
# v0.5.0 SOURCE COMMENTARY — Engineering/research utility
# Supports repeatable data generation, audio tests, game-file analysis, or Wine
# probing. Inspect command-line arguments and preserve user-owned game files.
set -euo pipefail
cd "$(dirname "$0")/.."
bash win32/build.sh
clang -std=c11 -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer tools/test_spatial_native.c -o /tmp/a3d-v027-spatial-test
clang -std=c11 -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer tools/test_measured_native.c -o /tmp/a3d-v029-measured-test
/tmp/a3d-v029-measured-test
clang -std=c11 -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer tools/test_binaural_native.c -o /tmp/a3d-v028-binaural-test
/tmp/a3d-v028-binaural-test
/tmp/a3d-v027-spatial-test
clang -std=c11 -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer tools/test_binaural_native.c -o /tmp/a3d-v028-binaural-test
/tmp/a3d-v028-binaural-test
# Standalone stateful multivoice and geometry/audio tests.
clang -std=c11 -O1 -g -Wall -Wextra -Werror -Wno-unused-function -fsanitize=address,undefined -fno-omit-frame-pointer tools/test_stream_native.c -o /tmp/alice-a3d31-stream
/tmp/alice-a3d31-stream
clang -std=c11 -O1 -g -Wall -Wextra -Werror -Wno-unused-function -fsanitize=address,undefined -fno-omit-frame-pointer tools/test_stream_scene_native.c -o /tmp/alice-a3d31-scene
/tmp/alice-a3d31-scene
clang -std=c11 -O1 -g -Wall -Wextra -Werror -Wno-unused-function -fsanitize=address,undefined -fno-omit-frame-pointer tools/test_game_spatial_native.c -o /tmp/alice-a3d41-game-spatial
/tmp/alice-a3d41-game-spatial
cmake -S acoustics -B build-acoustics -DCMAKE_BUILD_TYPE=Release
cmake --build build-acoustics --parallel 2
ctest --test-dir build-acoustics --output-on-failure
python3 -m unittest discover -s tools -p 'test_*.py' -v
# App-local manifest, installer safety, and legacy A3dCreate PE32 ABI.
python3 -m unittest discover -s dropin/tests -p 'test_*.py' -v
