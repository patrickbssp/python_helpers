#/bin/bash

# Create checksum for MP3s and Waves and compare them

# Take checksums of Take1, Take2, and wave files
md5sum Take1/* > Take1.md5;
md5sum Take2/* > Take2.md5;
md5sum *.wav > wav.md5; more wav.md5

# Compare Take1 and Take2 (should differ due to different folder names)
diff Take1.md5 Take2.md5;
echo "diff: $?"

# Replace Take2 with Take1 in Take2.md5
sed -i s/Take2/Take1/ Take2.md5

# Compare Take1 and Take2 again (should match now)
diff Take1.md5 Take2.md5
echo "diff: $?"
