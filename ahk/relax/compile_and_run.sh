TempSource=/tmp/source.rlx
TempOutput=/tmp/output.elf
cat - > $TempSource

cd /ahk/relax
ErrorText=$(build/compiler.elf -i $TempSource -o $TempOutput --elf --no-colors 2>&1 >/dev/null)

if [ -n "$ErrorText" ]
then
	echo "$ErrorText"
	exit 1
fi

cd /tmp
chmod +x "$TempOutput"
RunOutput=$($TempOutput)

echo "Exit code: $?"
echo "$RunOutput"

rm "$TempSource"
rm "$TempOutput"

