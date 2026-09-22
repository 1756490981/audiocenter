using System.Runtime.InteropServices;

namespace AudioHelper;

[ComImport]
[Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface IPropertyStore
{
	int GetCount(out int propCount);

	int GetAt(int index, out PROPERTYKEY key);

	int GetValue(ref PropertyKey key, out PROPVARIANT value);

	int SetValue(ref PropertyKey key, ref PROPVARIANT value);

	int Commit();
}
