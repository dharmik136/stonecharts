# Antigravity Performance & Resource Utilization Benchmarking Specification

> [!WARNING]
> Superseded research artifact - not an approved product commitment. The approved
> post-0.0.0.4 direction is governed by
> `docs/product/visual-integrity-strategy.md`,
> `docs/product/capability-matrix.md`, and DEC-017.

## 1. Executive Summary & Objectives
This document establishes the official benchmarking specification and performance validation framework for the Antigravity visualization rendering engine. It defines the metrics, workloads, architectural comparison methodologies, and validation criteria (SLAs/SLOs) required to evaluate:
- **Native Renderers**: Python-native (e.g., Matplotlib/Plotly/custom bindings) and Go-native (e.g., custom SVG/Canvas engines).
- **Export Servers**: JavaScript/Node.js/Puppeteer-based wrappers (Vega-CLI, Highcharts Export Server).

The primary objective is to guarantee rendering efficiency, resource containment, and low latency across local client environments and distributed server-side clusters.

---

## 2. Architectural Paradigm Comparison
To set the context for the benchmarking metrics, the system compares two main execution paths:

### 2.1 Native Rendering Path (Python / Go)
- **Runtime**: Native binary execution or direct interpreter memory.
- **Process Model**: Single or multi-threaded in-process execution.
- **Execution Overhead**: Minimal. Direct compilation/execution of rendering code. Direct output compilation to target format (SVG/PNG/PDF).
- **Security & Sandboxing**: Standard OS process containment. No browser runtime required.

### 2.2 Export Server Path (Vega / Highcharts)
- **Runtime**: Node.js/Java executing inside a container.
- **Process Model**: Headless browser (Chromium/Puppeteer) spawn or worker thread pool.
- **Execution Overhead**: High serialization overhead (JSON serialization of data/spec, IPC/network call to export service, headless page navigation, CSS parsing, DOM layout, canvas image extraction, network response).
- **Security & Sandboxing**: Complex browser sandbox configuration.

### 2.3 Architecture Execution Flow
```mermaid
graph TD
    subgraph Native Rendering (Python/Go)
        A1[Input Data Spec] --> A2[Native Engine Logic]
        A2 --> A3[Canvas/SVG Output Compiler]
        A3 --> A4[Output File]
    end

    subgraph Export Server Rendering (Vega/Highcharts)
        B1[Input Data Spec] --> B2[JSON Serialization]
        B2 --> B3[HTTP/gRPC/IPC Post]
        B3 --> B4[Headless Browser / Node Worker]
        B4 --> B5[DOM/CSS Rendering Engine]
        B5 --> B6[Rasterization / SVG Generation]
        B6 --> B7[Network Response/Deserialization]
        B7 --> B8[Output File]
    end
```

---

## 3. Key Metrics & Instrumentation

We evaluate performance across four key resource domains:

| Metric Group | Metric Name | Metric Unit | Collection Method | Key Focus |
| :--- | :--- | :--- | :--- | :--- |
| **Execution Latency** | `Latency_Total` | Milliseconds (ms) | Wall clock time (P50, P95, P99) | End-to-end responsiveness |
| | `Latency_Compute` | Milliseconds (ms) | CPU Time (User + System) | Core rendering loop execution |
| **Compute Overhead** | `CPU_Cycles` | Clock cycles / Ticks | POSIX `getrusage` / Windows Performance Counters | CPU footprint per render |
| **Memory footprint** | `Peak_RSS` | Megabytes (MB) | Resident Set Size (RSS) peak | Physical memory pressure |
| | `Peak_VMS` | Megabytes (MB) | Virtual Memory Size (VMS) peak | Virtual memory mapping |
| **Output efficiency** | `Output_Size` | Kilobytes (KB) | Disk / Stream write bytes count | Bandwidth & storage efficiency |

### 3.1 Latency Profiling
Latency must be captured at multiple telemetry boundaries:
- **Serialization Latency**: Time spent converting native structures to transfer formats (e.g., JSON).
- **Transport Latency**: Time spent across IPC/HTTP bounds (applicable to Export Servers).
- **Rendering Latency**: Time spent by the renderer layout and drawing engines.

### 3.2 Memory Footprint Monitoring
Peak RSS (Resident Set Size) represents the maximum physical memory occupied by the process during rendering:
- For Native Go: Monitored via `runtime.ReadMemStats` and external OS process monitoring.
- For Native Python: Monitored via the `tracemalloc` module and `resource.getrusage`.
- For Export Servers: Must monitor the parent Node/Java process, the network interface, AND all child browser helper processes (Chromium/Puppeteer helper subprocesses).

> [!WARNING]
> Failing to track subprocesses (e.g., Puppeteer helper processes) under headless browser configurations will lead to severely underreported Peak RSS metrics. Measurement tools must crawl the process tree.

---

## 4. Benchmarking Methodology

To ensure consistency and prevent run-to-run variance, tests must adhere to standard conditions.

### 4.1 Environment Standardization
- **CPU Pinning**: Pin benchmark runs to specific cores to avoid context-switching overhead.
- **Run Count**: Each workload must be run a minimum of $N = 100$ iterations.
- **Warm-up Phase**: Pre-run the pipeline $W = 10$ times to allow JIT, library cache loading, and TCP connection pooling (for servers) to stabilize.
- **Isolation**: Disable power-saving states and background daemon processes during measurement.

### 4.2 Test Workloads Specification

We define three target workloads:

#### Small Workload (Simple Chart)
- **Data Points**: 100 rows, 2 columns (x, y).
- **Chart Type**: Single-series Line or Bar chart.
- **Complexity**: Zero interactive elements, standard typography, basic labels.
- **Objective**: Establish baseline startup and rendering overhead.

#### Medium Workload (Complex Dashboard Component)
- **Data Points**: 5,000 rows, 5 columns (timestamp, metric_a, metric_b, category, group).
- **Chart Type**: Multi-series Line Chart with markers, Grid layout, Dual-Axis.
- **Complexity**: Complex styling, custom color palettes, grid lines, legends, and static hover templates.
- **Objective**: Simulate standard production user workloads.

#### Stress / Large Workload (High Density Visualization)
- **Data Points**: 100,000 rows, 3 columns (x, y, intensity).
- **Chart Type**: Large Heatmap or Scatter Plot.
- **Complexity**: High opacity overlays, dynamic grid binning, complex clipping paths.
- **Objective**: Identify memory leaks, CPU saturation levels, and buffer rendering bottlenecks.

---

## 5. Performance Validation Criteria (SLAs/SLOs)

All rendering modifications must validate against these metrics in automated CI/CD pipelines before merge approvals.

### 5.1 Native Rendering vs. Export Server Performance Gates

The target performance boundaries are summarized below:

| Workload | Metric | Go Native Target | Python Native Target | Vega Export Server Target |
| :--- | :--- | :--- | :--- | :--- |
| **Small** | Latency (P95) | $\le 15$ ms | $\le 45$ ms | $\le 300$ ms |
| | Peak RSS | $\le 25$ MB | $\le 65$ MB | $\le 250$ MB |
| | Output Size (SVG) | $\le 15$ KB | $\le 20$ KB | $\le 30$ KB |
| **Medium** | Latency (P95) | $\le 45$ ms | $\le 120$ ms | $\le 650$ ms |
| | Peak RSS | $\le 45$ MB | $\le 120$ MB | $\le 400$ MB |
| | Output Size (SVG) | $\le 120$ KB | $\le 135$ KB | $\le 150$ KB |
| **Stress** | Latency (P95) | $\le 350$ ms | $\le 950$ ms | $\le 3200$ ms |
| | Peak RSS | $\le 120$ MB | $\le 280$ MB | $\le 850$ MB |
| | Output Size (SVG) | $\le 1.8$ MB | $\le 2.0$ MB | $\le 2.5$ MB |

> [!NOTE]
> Highcharts and Vega Export Servers incur a fixed latency tax of approximately 150–250ms due to HTTP round-trip serialization and headless browser startup context switching. Native renderers must outperform export servers by at least a factor of 5x.

### 5.2 CI/CD Quality Gates
1. **Regress Check**: Any PR that causes a latency regression $> 10\%$ in any category will fail the performance check.
2. **Leakage Check**: Run the workload sequentially 500 times. Memory usage must return to baseline ($0\%$ drift, excluding garbage collection cycles). Any sustained RSS increase indicates memory leak regression.
3. **Output File Payload Limit**: Generated SVG payloads must not include duplicate CSS classes or redundant path variables, capped strictly by the limits defined in Section 5.1.
