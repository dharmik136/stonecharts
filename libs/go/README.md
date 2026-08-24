# StoneCharts Go renderer

The Go renderer is a repository-local module used for deterministic parity and
qualification against the Python renderer.

```bash
go test ./...
go run ./cmd/line_basic ../../charts/line-basic/examples/basic.json out.svg out.html
```

The canonical product version `0.0.0.34` has four numeric components and is not a Go
semantic version. There is no authorized public module path or supported `go get`
command. Do not create or consume a fabricated `v0.0.0.34` tag; public Go distribution
requires the ecosystem mapping mandated by repository ADR 0007.
