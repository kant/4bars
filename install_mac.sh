brew install gbevin/tools/sendmidi
brew install gbevin/tools/receivemidi
brew install liblo
brew install figlet
rm /usr/local/bin/4bars
ln -s $(pwd)/4bars.sh /usr/local/bin/4bars
chmod +x /usr/local/bin/4bars
