// Command line_basic renders a spec JSON to SVG (stdout) and, optionally, HTML.
//
// Usage (run from libs/go):
//
//	go run ./cmd/line_basic <spec.json>                 # SVG to stdout
//	go run ./cmd/line_basic <spec.json> <out.svg> <out.html>
package main

import (
	"fmt"
	"os"

	"peakcharts"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: line_basic <spec.json> [out.svg] [out.html]")
		os.Exit(2)
	}
	b, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	spec, err := peakcharts.FromJSON(b)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	svg := peakcharts.RenderSVG(spec)

	if len(os.Args) >= 3 {
		if err := os.WriteFile(os.Args[2], []byte(svg), 0o644); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	} else {
		fmt.Print(svg)
	}
	if len(os.Args) >= 4 {
		if err := peakcharts.SaveHTML(spec, os.Args[3], ""); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
}
