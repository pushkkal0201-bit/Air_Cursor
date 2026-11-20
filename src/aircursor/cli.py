"""Command-line launcher for AirCursor's local or explicitly enabled LAN server."""
from __future__ import annotations

import argparse
import os

from .server import VERSION, create_app, normalize_tailscale_hostname


def port_number(value):
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1024 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1024 and 65535")
    return port


def make_parser():
    parser = argparse.ArgumentParser(
        prog="aircursor",
        description="A paired mouse and presentation remote for your own devices."
    )
    parser.add_argument("--version", action="version", version="AirCursor " + VERSION)
    network = parser.add_mutually_exclusive_group()
    network.add_argument("--lan", action="store_true",
                         help="listen on the private network (explicit opt-in)")
    network.add_argument("--local-only", action="store_true",
                         help="bind only to localhost (default)")
    parser.add_argument("--host", help="advanced: explicitly specify the bind address")
    parser.add_argument("--port", type=port_number, default=None,
                        help="TCP port, default 5055")
    parser.add_argument("--tailscale-host", metavar="DEVICE.TAILNET.TS.NET",
                        help="enable trusted Tailscale Serve HTTPS mode, keep backend on localhost")
    parser.add_argument("--https", action="store_true",
                        help="development-only self-signed HTTPS certificate")
    return parser


def main(argv=None):
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        port = port_number(str(args.port or os.environ.get("AIRCURSOR_PORT", "5055")))
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    tailscale_host = None
    if args.tailscale_host:
        try:
            tailscale_host = normalize_tailscale_hostname(args.tailscale_host)
        except ValueError as exc:
            parser.error(str(exc))
        if args.lan or args.host or args.https or os.environ.get("AIRCURSOR_HTTPS") == "1":
            parser.error("--tailscale-host cannot be combined with --lan, --host, or --https")
        if os.environ.get("AIRCURSOR_HOST") not in (None, "", "127.0.0.1", "localhost"):
            parser.error("--tailscale-host requires a localhost-only bind address")
        host = "127.0.0.1"
    elif args.local_only:
        host = "127.0.0.1"
    elif args.lan:
        host = "0.0.0.0"
    else:
        host = args.host or os.environ.get("AIRCURSOR_HOST") or "127.0.0.1"
    if args.local_only and args.host:
        parser.error("--local-only cannot be combined with --host")
    if args.lan and args.host:
        parser.error("--lan cannot be combined with --host")
    if any(char.isspace() for char in host):
        parser.error("host cannot contain whitespace")
    os.environ["AIRCURSOR_HOST"] = host
    os.environ["AIRCURSOR_PORT"] = str(port)
    if args.https:
        os.environ["AIRCURSOR_HTTPS"] = "1"
    https = os.environ.get("AIRCURSOR_HTTPS", "0") == "1"
    app = create_app(tailscale_host=tailscale_host) if tailscale_host else create_app()
    scheme = "https" if https else "http"
    print("\nAirCursor {} — private remote controls".format(VERSION), flush=True)
    print("PAIRING PIN: {}".format(app.config["PAIRING_PIN"]), flush=True)
    print("Open {}://127.0.0.1:{}".format(scheme, port), flush=True)
    if tailscale_host:
        print("Phone HTTPS URL: https://{}".format(tailscale_host), flush=True)
        print("Tailscale Serve must be enabled separately: tailscale serve --bg {}".format(port), flush=True)
        print("Backend stays bound to 127.0.0.1; do not use Funnel.", flush=True)
    elif host != "127.0.0.1":
        print("LAN access enabled. Restrict firewall access to your private Wi-Fi.", flush=True)
    else:
        print("Local-only mode. Add --lan to allow trusted devices on your private Wi-Fi.", flush=True)
    print("Press Ctrl+C to stop. Do not expose this server to the internet.\n", flush=True)
    app.run(host=host, port=port, debug=False, use_reloader=False,
            ssl_context="adhoc" if https else None)


if __name__ == "__main__":
    main()
