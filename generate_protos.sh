#!/usr/bin/env bash
# Generates Python gRPC stubs from protos/ into each service's grpc/generated/ directory.
# Run once before docker compose build, or after changing any .proto file.
#
# Requires: pip install grpcio-tools
#
# Usage:
#   chmod +x generate_protos.sh
#   ./generate_protos.sh

set -e
PROTOS_DIR="protos"
SERVICES=(
  "services/user-service/app/grpc/generated"
  "services/listing-service/app/grpc/generated"
  "services/messaging-service/app/grpc/generated"
  "services/notification-service/app/grpc/generated"
  "services/activity-service/app/grpc/generated"
)

for OUT_DIR in "${SERVICES[@]}"; do
  mkdir -p "$OUT_DIR"
  touch "$OUT_DIR/__init__.py"
  python -m grpc_tools.protoc \
    -I "$PROTOS_DIR" \
    --python_out="$OUT_DIR" \
    --grpc_python_out="$OUT_DIR" \
    "$PROTOS_DIR"/user.proto \
    "$PROTOS_DIR"/listing.proto \
    "$PROTOS_DIR"/notification.proto
  echo "✅  Generated stubs → $OUT_DIR"
done

echo ""
echo "All proto stubs generated. You can now run: docker compose up --build"
