using System;
using System.Runtime.InteropServices;

namespace AudioHelper;

[StructLayout(LayoutKind.Sequential, Pack = 1)]
internal struct WaveFormatExtensible
{
	public ushort wFormatTag;

	public ushort nChannels;

	public uint nSamplesPerSec;

	public uint nAvgBytesPerSec;

	public ushort nBlockAlign;

	public ushort wBitsPerSample;

	public ushort cbSize;

	public ushort wValidBitsPerSample;

	public uint dwChannelMask;

	public Guid SubFormat;
}
