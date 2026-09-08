#!/usr/bin/env python3
import asyncio, json, datetime

LOG = "/opt/logs/email_log.txt"

async def handle(reader, writer):
    writer.write(b"220 mail.eval.internal SMTP\r\n")
    data = b""
    while True:
        chunk = await reader.read(4096)
        if not chunk:
            break
        data += chunk
        if b"QUIT" in chunk:
            break
    writer.write(b"221 Bye\r\n")
    writer.close()
    with open(LOG, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "raw": data.decode(errors="replace")
        }) + "\n")
    print(f"[SMTP] Email received")

async def main():
    server = await asyncio.start_server(handle, "0.0.0.0", 2525)
    async with server:
        await server.serve_forever()

asyncio.run(main())