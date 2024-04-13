# Scaling tool

Creates / Deletes new nodes on gRPC requests

```proto
service Scaler {
    rpc CreateNode(CreateNodeRequest) returns (CreateNodeResponse) {}
    rpc DeleteNode(DeleteNodeRequest) returns (DeleteNodeResponse) {}
    rpc ListNodes() returns (ListNodesResponse) {}
}
```

