using System;

namespace AudioHelper;

internal struct PROPERTYKEY
{
	public Guid fmtid;

	public int pid;
}
internal struct PropertyKey(Guid f, int p)
{
	public Guid fmtid = f;

	public int pid = p;
}
