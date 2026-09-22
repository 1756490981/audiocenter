using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("6D2EF506-78F5-448D-878D-984D4E1C8E2F")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IPartsList
{
	int GetCount(out uint count);

	int GetPart(uint index, out nint part);
}
