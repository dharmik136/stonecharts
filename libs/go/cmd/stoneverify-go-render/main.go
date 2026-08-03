// Command stoneverify-go-render is the StoneVerify Go renderer adapter.
//
// Contract:
//   - stoneverify-go-render <spec.json> writes the rendered SVG to stdout.
//   - stoneverify-go-render --version writes machine-readable version fields.
//   - failures write a diagnostic to stderr and exit non-zero.
package main

import (
	"fmt"
	"os"

	"stonecharts"
)

const adapterVersion = "1.0.0"

func main() {
	if len(os.Args) == 2 && os.Args[1] == "--version" {
		fmt.Printf("stoneverify-go-render adapter=%s stonecharts=%s module=stonecharts\n", adapterVersion, stonecharts.Version)
		return
	}
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: stoneverify-go-render <spec.json>")
		os.Exit(2)
	}
	b, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	spec, err := stonecharts.FromJSON(b)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	svg, err := stonecharts.RenderSVG(spec)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Print(svg)
}
