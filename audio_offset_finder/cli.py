# audio-offset-finder
#
# Copyright (c) 2014-23 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .audio_offset_finder import find_offset_between_files
import argparse
import sys


def main(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Find the offset of one audio file within another.\n"
            "Returns the offset in seconds from the start of the 'within' file to the start of the 'offset-of' one.\n"
            "A negative offset implies that the 'within' file starts after the 'offset-of' one.\n\n"
            "Also returns the 'standard score' of the correlation peak.  Scores >10 imply a good probability that "
            "the offset is accurate to within the precision of the tool (around 0.01s, adjustable)"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--find-offset-of", metavar="audio file", type=str, help="Find the offset of file")
    parser.add_argument("--within", metavar="audio file", type=str, help="Within file")
    parser.add_argument("--sr", metavar="sample rate", type=int, default=8000, help="Target sample rate during downsampling")
    parser.add_argument(
        "--trim", metavar="seconds", type=int, default=60 * 15, help="Only uses first n seconds of audio files"
    )
    parser.add_argument(
        "--resolution", metavar="samples", type=int, default=128, help="Resolution (maximum accuracy) of search in samples"
    )
    parser.add_argument("--show-plot", action="store_true", dest="show_plot", help="Display plot of cross-correlation results")
    parser.add_argument(
        "--save-plot",
        metavar="plot file",
        dest="plot_file",
        type=str,
        help=("Save a plot of cross-correlation results to a file " "(format matches extension - png, ps, pdf, svg)"),
    )
    parser.add_argument("--json", action="store_true", dest="output_json", help="Output in JSON for further processing")
    args = parser.parse_args(argv)
    if not (args.find_offset_of and args.within):
        parser.error("Please provide input audio files")
    results = find_offset_between_files(
        args.within, args.find_offset_of, fs=int(args.sr), trim=int(args.trim), hop_length=int(args.resolution)
    )

    if args.output_json:
        import json

        json_results = {"time_offset": results["time_offset"], "standard_score": results["standard_score"]}
        print(json.dumps(json_results))
    else:
        print("Offset: %s (seconds)" % str(results["time_offset"]))
        print("Standard score: %s" % str(results["standard_score"]))

    if args.show_plot or args.plot_file is not None:
        plot_results(args, results)


# Re-order the cross-correlation array so that the zero offset is in the middle
def reorder_correlations(cc):
    from numpy import concatenate

    num_elements = len(cc)
    centre_index = int(num_elements / 2)
    return concatenate((cc[centre_index:], cc[:centre_index]))


def plot_results(args, results):
    import matplotlib.pyplot as pyplot
    import matplotlib.ticker as ticker

    cc = results["correlation"]
    cc_length = len(cc)
    plot_data = reorder_correlations(cc)

    pyplot.figure(figsize=(15, 5))
    xaxis_range = range(results["earliest_frame_offset"], results["latest_frame_offset"])
    pyplot.plot(xaxis_range, plot_data)

    ax = pyplot.gca()
    # Scale x values from frame numbers to time: t = mx + c, but c=0 for a symetrical cross-correlation
    m = results["time_scale"]
    ticks_x = ticker.FuncFormatter(lambda x, pos: "{0:g}".format(x * m))
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins="auto"))
    ax.xaxis.set_major_formatter(ticks_x)
    ax.set_xlabel("Time offset /s", fontsize="12")
    ax.set_ylabel("Cross-correlation coefficient", fontsize="12")
    ax.set(yticklabels=[])
    ax.tick_params(left=False)

    plot_title = "Offset of %s in %s" % (args.find_offset_of, args.within)
    pyplot.title(plot_title, fontsize=14)

    peak_xvalue = results["frame_offset"]
    if peak_xvalue > cc_length / 2:
        peak_xvalue -= cc_length

    pyplot.axvline(x=peak_xvalue, color="red", linestyle="dotted")

    if args.plot_file is not None:
        pyplot.savefig(args.plot_file)
    if args.show_plot:
        pyplot.show()


def run():
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    run()
