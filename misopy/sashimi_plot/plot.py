##
## sashimi-plot
##
## Utility for visualizing RNA-Seq densities along gene models and
## for plotting MISO output
##

import os
import matplotlib

import pysam
import shelve

import misopy
import misopy.gff_utils as gff_utils
import misopy.pe_utils as pe_utils

from misopy.samples_utils import load_samples, parse_sampler_params
from misopy.sashimi_plot.Sashimi import Sashimi
from misopy.sashimi_plot.plot_utils.samples_plotter import SamplesPlotter
from misopy.sashimi_plot.plot_utils.plotting import *
from misopy.sashimi_plot.plot_utils.plot_gene import plot_density_from_file
import matplotlib.pyplot as plt
from matplotlib import rc


def plot_event(event_name, pickle_dir, settings_filename,
               output_dir):
    """
    Visualize read densities across the exons and junctions
    of a given MISO alternative RNA processing event.

    Also plots MISO estimates and Psi values.
    """
    # Retrieve the full pickle filename
    genes_filename = os.path.join(pickle_dir,
                                  "genes_to_filenames.shelve")

    if not os.path.isfile(genes_filename):
        raise Exception, "Cannot find file %s. Are you sure the events " \
              "were indexed with the latest version of index_gff.py?" \
              %(genes_filename)
    
    event_to_filenames = shelve.open(genes_filename)
    if event_name not in event_to_filenames:
        raise Exception, "Event %s not found in pickled directory %s. " \
              "Are you sure this is the right directory for the event?" \
              %(event_name, pickle_dir)
    
    pickle_filename = event_to_filenames[event_name]

    plot_density_from_file(settings_filename, pickle_filename, event_name,
                           output_dir)


def plot_insert_len(insert_len_filename,
                    settings_filename,
                    output_dir):
    """
    Plot insert length distribution.
    """
    plot_name = os.path.basename(insert_len_filename)
    
    sashimi_obj = Sashimi(plot_name, output_dir,
                          settings_filename=settings_filename)

    settings = sashimi_obj.settings
    num_bins = settings["insert_len_bins"]
    output_filename = sashimi_obj.output_filename
    s = plt.subplot(1, 1, 1)
    
    print "Plotting insert length distribution..."
    print "  - Distribution file: %s" %(insert_len_filename)
    print "  - Output plot: %s" %(output_filename)
    
    insert_dist, params = pe_utils.load_insert_len(insert_len_filename)

    mean, sdev, dispersion, num_pairs \
          = pe_utils.compute_insert_len_stats(insert_dist)
    print "min insert: %.1f" %(min(insert_dist))
    print "max insert: %.1f" %(max(insert_dist))
    plt.title("%s (%d read-pairs)" \
              %(plot_name,
                num_pairs),
              fontsize=10)
    plt.hist(insert_dist, bins=num_bins, color='k',
             edgecolor="#ffffff", align='mid')
    axes_square(s)
    ymin, ymax = s.get_ylim()
    plt.text(0.05, 0.95, "$\mu$: %.1f\n$\sigma$: %.1f\n$d$: %.1f" \
             %(round(mean, 2),
               round(sdev, 2),
               round(dispersion, 2)),
             horizontalalignment='left',
             verticalalignment='top',
             bbox=dict(edgecolor='k', facecolor="#ffffff",
                       alpha=0.5),
             fontsize=10,
             transform=s.transAxes)
    plt.xlabel("Insert length (nt)")
    plt.ylabel("No. read pairs")
    sashimi_obj.save_plot()
        

def plot_posterior(miso_filename, settings_filename, output_dir):
    """
    Plot posterior distribution.
    """
#    samples, log_scores, params, gene = load_samples(miso_filename)
    samples, h, log_scores, sampled_map,\
             sampled_map_log_score, counts_info = load_samples(miso_filename)
    params = parse_sampler_params(miso_filename)
    
    sp = SamplesPlotter(samples, params)
    
    if with_intervals != None:
        with_intervals = float(with_intervals)/100.
        print "Plotting with %d-percent confidence intervals" %(int(with_intervals * 100))
    else:
        with_intervals = False

    if plot_mean:
        print "Plotting mean of posterior."

    print "Plotting posterior distribution..."
    print "  - MISO event file: %s" %(miso_filename)
    print "  - Output dir: %s" %(output_dir)
    
    sp.plot(plot_intervals=with_intervals, fig_dims=dimensions,
            plot_mean=plot_mean)

    # Determine output format type
    # if not png:
    #     matplotlib.use('PDF')
    #     plt.rcParams['ps.useafm'] = True
    #     plt.rcParams['pdf.fonttype'] = 42
    #     file_ext = ".pdf"
    # else:
    #     file_ext = ".png"

    # output_filename = os.path.join(output_dir,
    #                                os.path.basename(miso_filename).replace(".miso",
    #                                                                        file_ext))
    # print "Outputting plot to: %s" %(output_filename)
    # plt.savefig(output_filename)
    

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--plot-posterior", dest="plot_posterior", nargs=2, default=None,
                      help="Plot the posterior distribution. Takes the arguments: (1) a raw MISO output "
                      "file (.miso), (2) a settings filename.")
    parser.add_option("--plot-insert-len", dest="plot_insert_len", nargs=2, default=None,
                      help="Plot the insert length distribution from a given insert length (*.insert_len) "
                      "filename.")
    parser.add_option("--plot-bf-dist", dest="plot_bf_dist", nargs=2, default=None,
                      help="Plot Bayes factor distributon. Takes the arguments: "
                      "(1) Bayes factor filename (*.miso_bf) settings filename, "
                      "(2) a settings filename.")
    parser.add_option("--plot-event", dest="plot_event", nargs=3, default=None,
                      help="Plot read densities and MISO inferences for a given alternative event. "
                      "Takes the arguments: (1) event name (i.e. the ID= of the event based on MISO gff3 "
                      "annotation file, (2) directory where MISO output is for that event type (e.g. if event is a "
                      "skipped exon, provide the directory where the output for all SE events are), "
                      "(3) path to plotting settings file.")
    parser.add_option("--output-dir", dest="output_dir", nargs=1, default=None,
                      help="Output directory.")
    (options, args) = parser.parse_args()

    if options.output_dir == None:
        print "Error: need --output-dir"
        return

    output_dir = os.path.abspath(os.path.expanduser(options.output_dir))

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    if options.plot_insert_len != None:
        insert_len_filename = os.path.abspath(os.path.expanduser(options.plot_insert_len[0]))
        settings_filename = os.path.abspath(os.path.expanduser(options.plot_insert_len[1]))
        plot_insert_len(insert_len_filename, settings_filename, output_dir)

    if options.plot_posterior != None:
        miso_filename = os.path.abspath(os.path.expanduser(options.plot_posterior[0]))
        settings_filename = os.path.abspath(os.path.expanduser(options.plot_posterior[1]))
        plot_posterior(miso_filename, settings_filename, output_dir)

    if options.plot_event != None:
        event_name = options.plot_event[0]
        pickle_dir = os.path.abspath(os.path.expanduser(options.plot_event[1]))
        settings_filename = os.path.abspath(os.path.expanduser(options.plot_event[2]))
        plot_event(event_name, pickle_dir, settings_filename, output_dir)
        

if __name__ == '__main__':
    main()