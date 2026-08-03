package stonecharts

import (
	"fmt"
	"unicode/utf8"
)

const (
	MaxSpecBytes       = 1000000
	MaxSeries          = 50
	MaxPointsPerSeries = 10000
	MaxTotalPoints     = 50000
	MaxLabelLength     = 512
	MaxSVGBytes        = 5000000
)

type ResourceLimitError struct {
	Code     string
	Path     string
	Limit    int
	Received int
}

func (e *ResourceLimitError) Error() string {
	return fmt.Sprintf("%s: %s: limit %d exceeded, received %d", e.Code, e.Path, e.Limit, e.Received)
}

func checkLabelLimit(v interface{}, path string) error {
	if s, ok := v.(string); ok && utf8.RuneCountInString(s) > MaxLabelLength {
		return &ResourceLimitError{Code: "LIMIT.LABEL_LENGTH", Path: path, Limit: MaxLabelLength, Received: utf8.RuneCountInString(s)}
	}
	return nil
}

func enforceSpecLimits(spec interface{}, rawSizeHint int) error {
	if rawSizeHint > MaxSpecBytes {
		return &ResourceLimitError{Code: "LIMIT.SPEC_BYTES", Path: "$", Limit: MaxSpecBytes, Received: rawSizeHint}
	}
	d, ok := spec.(map[string]interface{})
	if !ok {
		return nil
	}
	for _, key := range []string{"id", "title", "subtitle"} {
		if err := checkLabelLimit(d[key], "$."+key); err != nil {
			return err
		}
	}
	for _, axisName := range []string{"xAxis", "yAxis", "secondaryYAxis"} {
		axis, ok := d[axisName].(map[string]interface{})
		if !ok {
			continue
		}
		if err := checkLabelLimit(axis["title"], "$."+axisName+".title"); err != nil {
			return err
		}
		if categories, ok := axis["categories"].([]interface{}); ok {
			for i, category := range categories {
				if err := checkLabelLimit(category, "$."+axisName+".categories["+itoa(i)+"]"); err != nil {
					return err
				}
			}
		}
	}
	series, ok := d["series"].([]interface{})
	if !ok {
		return nil
	}
	if len(series) > MaxSeries {
		return &ResourceLimitError{Code: "LIMIT.SERIES_COUNT", Path: "$.series", Limit: MaxSeries, Received: len(series)}
	}
	totalPoints := 0
	for seriesIndex, item := range series {
		m, ok := item.(map[string]interface{})
		if !ok {
			continue
		}
		if err := checkLabelLimit(m["name"], "$.series["+itoa(seriesIndex)+"].name"); err != nil {
			return err
		}
		data, ok := m["data"].([]interface{})
		if !ok {
			continue
		}
		if len(data) > MaxPointsPerSeries {
			return &ResourceLimitError{Code: "LIMIT.POINTS_PER_SERIES", Path: "$.series[" + itoa(seriesIndex) + "].data", Limit: MaxPointsPerSeries, Received: len(data)}
		}
		totalPoints += len(data)
		if totalPoints > MaxTotalPoints {
			return &ResourceLimitError{Code: "LIMIT.TOTAL_POINTS", Path: "$.series[*].data", Limit: MaxTotalPoints, Received: totalPoints}
		}
	}
	return nil
}

func enforceSVGLimit(svg string) error {
	size := len([]byte(svg))
	if size > MaxSVGBytes {
		return &ResourceLimitError{Code: "LIMIT.SVG_BYTES", Path: "$.svg", Limit: MaxSVGBytes, Received: size}
	}
	return nil
}
