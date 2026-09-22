using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IAudioSessionEnumerator
{
	int GetCount(out int count);

	int GetSession(int index, out nint session);
}
