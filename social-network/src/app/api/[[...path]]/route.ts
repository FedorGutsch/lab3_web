import { NextRequest, NextResponse } from "next/server";

const API_BASE = "http://127.0.0.1:3001";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  return proxyRequest(request, await params);
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  return proxyRequest(request, await params);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  return proxyRequest(request, await params);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path?: string[] }> }
) {
  return proxyRequest(request, await params);
}

async function proxyRequest(
  request: NextRequest,
  params: { path?: string[] }
) {
  const pathSegments = params.path || [];
  const path = pathSegments.join("/");
  const url = `${API_BASE}/api/${path}`;

  // Forward query params
  const searchParams = request.nextUrl.searchParams.toString();
  const fullUrl = searchParams ? `${url}?${searchParams}` : url;

  // Forward headers
  const headers: Record<string, string> = {};
  request.headers.forEach((value, key) => {
    if (key.toLowerCase() !== "host" && key.toLowerCase() !== "connection") {
      headers[key] = value;
    }
  });

  // Forward body for POST/PUT
  let body: string | undefined;
  if (request.method === "POST" || request.method === "PUT") {
    body = await request.text();
  }

  try {
    const res = await fetch(fullUrl, {
      method: request.method,
      headers,
      body,
    });

    const data = await res.text();
    return new NextResponse(data, {
      status: res.status,
      headers: {
        "Content-Type": res.headers.get("Content-Type") || "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Backend unavailable" },
      { status: 502 }
    );
  }
}
