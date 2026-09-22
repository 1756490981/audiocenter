using System;
using System.Runtime.InteropServices;

namespace AudioHelper;

[StructLayout(LayoutKind.Explicit, Size = 24)]
internal struct PROPVARIANT
{
	[FieldOffset(0)]
	public short vt;

	[FieldOffset(8)]
	public nint value;

	[FieldOffset(8)]
	public uint blobSize;

	[FieldOffset(16)]
	public nint blobData;

	public object Value
	{
		get
		{
			if (vt == 31)
			{
				return Marshal.PtrToStringUni(value) ?? "";
			}
			if ((vt == 65 || vt == 4113) && blobData != IntPtr.Zero && blobSize != 0)
			{
				byte[] array = new byte[blobSize];
				Marshal.Copy(blobData, array, 0, (int)blobSize);
				return array;
			}
			return value;
		}
	}

	public static PROPVARIANT FromString(string s)
	{
		if (s == null)
		{
			return new PROPVARIANT
			{
				vt = 1
			};
		}
		return new PROPVARIANT
		{
			vt = 31,
			value = Marshal.StringToCoTaskMemUni(s)
		};
	}

	public static PROPVARIANT FromBlob(byte[] data)
	{
		PROPVARIANT result = new PROPVARIANT
		{
			vt = 65,
			blobSize = (uint)data.Length,
			blobData = Marshal.AllocCoTaskMem(data.Length)
		};
		Marshal.Copy(data, 0, result.blobData, data.Length);
		return result;
	}

	public static PROPVARIANT FromBool(bool b)
	{
		return new PROPVARIANT
		{
			vt = 11,
			value = new IntPtr(b ? (-1) : 0)
		};
	}

	public void FreeBlob()
	{
		if ((vt == 65 || vt == 4113) && blobData != IntPtr.Zero)
		{
			Marshal.FreeCoTaskMem(blobData);
		}
	}

	public void FreeString()
	{
		if (vt == 31 && value != IntPtr.Zero)
		{
			Marshal.FreeCoTaskMem(value);
		}
	}
}
