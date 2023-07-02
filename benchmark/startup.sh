#!/bin/bash
source ~/.cargo/env &&
cargo run --example origin &
RUST_LOG=soldr=trace cargo run
wait
curl -vvv -H "Content-Type: application/json" localhost:3443/origins \
-d '{ "domain": "example.wh.soldr.dev", "origin_uri": "http://localhost:8080" }'