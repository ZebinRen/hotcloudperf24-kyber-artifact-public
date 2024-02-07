import os.path
import matplotlib
import matplotlib.pyplot as plt

import numpy as np

# Switch to type 1 fonts
matplotlib.rcParams['text.usetex'] = True
plt.rc('font', **{'family': 'serif', 'serif': ['Times']})

m_color_index = 0
matplotlib_color = [
    '#0077BB', '#009988', '#EE7733', '#CC3311', '#EE3377', '#BBBBBB', '#000000'
]

dot_style = [
    '+',
    'X',
    'o',
    'v',
    's',
    'P',
]


def get_next_color():
    global m_color_index
    c = matplotlib_color[m_color_index]
    m_color_index += 1

    return c


def reset_color():
    global m_color_index
    m_color_index = 0


# Parameters
bar_width = 0.15

datalabel_size = 24
datalabel_va = 'bottom'
axis_tick_font_size = 36
axis_label_font_size = 44
legend_font_size = 30

group_list = ['50us-20us', '50us-100ms', '100ms-20us', '100ms-100ms']
r_lat_r1_w256 = {
    '50us-20us': [194.8, 178.4, 201.7],
    '50us-100ms': [160.4, 160.8, 160.8],
    '100ms-20us': [249.9, 184.9, 248.0],
    '100ms-100ms': [228.8, 182.9, 249.9],
}

w_thr_r1_w256 = {
    '50us-20us': [118.2, 105.3, 126.4],
    '50us-100ms': [72.9, 75.5, 73.3],
    '100ms-20us': [143.8, 116.0, 147.0],
    '100ms-100ms': [140.1, 113.9, 146.0],
}

r_thr_r256_w256 = {
    '50us-20us': [227.7, 234.4, 228.1],
    '50us-100ms': [231.0, 239.3, 234.6],
    '100ms-20us': [93.2, 229.7, 132.6],
    '100ms-100ms': [230.5, 239.1, 230.9],
}

w_thr_r256_w256 = {
    '50us-20us': [115.5, 104.3, 122.9],
    '50us-100ms': [65.6, 67.9, 65.6],
    '100ms-20us': [127.6, 107.8, 132.6],
    '100ms-100ms': [119.0, 108.7, 128.2],
}

x_ticks = [r'\textbf{ext4}', r'\textbf{f2fs}', r'\textbf{xfs}']

reset_color()
# rw-w256 read latency
if True:
    y_values = r_lat_r1_w256
    std_dev = None
    legend_label = {i: i for i in group_list}
    title = None
    xlabel = None
    ylabel = 'P99 latency~($\mu$s)'
    fig_save_path = 'samsung-r-lat-r1-w256.pdf'
    # plot
    fig, ax = plt.subplots(figsize=(12, 8))
    plt.grid(axis='y')  # x, y, both

    # x, y axis limit
    # ax.set_xlim(0, 2)
    # ax.set_ylim(0, 1.25)

    # set ticks
    plt.xticks(list(np.arange(len(x_ticks))), x_ticks)

    if title:
        plt.title(title)

    if xlabel:
        plt.xlabel(xlabel, fontsize=axis_label_font_size)
    if ylabel:
        plt.ylabel(ylabel, fontsize=axis_label_font_size)

    ax.tick_params(axis='both', which='major', labelsize=axis_tick_font_size)

    # compute bar offset, with respect to center
    bar_offset = []
    mid_point = (len(group_list) * bar_width) / 2
    for i in range(len(group_list)):
        bar_offset.append(bar_width * i + 0.5 * bar_width - mid_point)

    x_axis = np.arange(len(x_ticks))
    # draw figure by column
    for (index, group_name) in zip(range(len(group_list)), group_list):
        y = y_values[group_name]
        yerr = None
        if std_dev:
            yerr = std_dev[group_name]
        bar_pos = x_axis + bar_offset[index]

        plt.bar(bar_pos,
                y,
                width=bar_width,
                label=legend_label[group_name],
                yerr=yerr,
                color=get_next_color())

        # print data label
        for (x, y) in zip(bar_pos, y):
            text = '{:.0f}'.format(y)
            plt.text(
                x,
                y,
                text,
                size=datalabel_size,
                ha='center',
                va=
                datalabel_va,  # 'bottom', 'baseline', 'center', 'center_baseline', 'top'
            )

    # Legend: Change the ncol and loc to fine-tune the location of legend
    # if legend_label != None:
    #     plt.legend(fontsize=legend_font_size, loc='lower left', ncol=2)
    #     # plt.legend(fontsize=legend_font_size,
    #     #            ncol=2,
    #     #            loc='upper left',
    #     #            bbox_to_anchor=(0, 1.2),
    #     #            columnspacing=0.3)

    plt.savefig(fig_save_path, bbox_inches='tight')

reset_color()
# rw-w256 write throughput
if True:
    y_values = w_thr_r1_w256
    std_dev = None
    legend_label = {i: i for i in group_list}
    title = None
    xlabel = None
    ylabel = 'Throughput~(K IOPS)'
    fig_save_path = 'samsung-w-thr-r1-w256.pdf'
    # plot
    fig, ax = plt.subplots(figsize=(12, 8))
    plt.grid(axis='y')  # x, y, both

    # x, y axis limit
    # ax.set_xlim(0, 2)
    ax.set_ylim(0, 265)

    # set ticks
    plt.xticks(list(np.arange(len(x_ticks))), x_ticks)

    if title:
        plt.title(title)

    if xlabel:
        plt.xlabel(xlabel, fontsize=axis_label_font_size)
    if ylabel:
        plt.ylabel(ylabel, fontsize=axis_label_font_size)

    ax.tick_params(axis='both', which='major', labelsize=axis_tick_font_size)

    # compute bar offset, with respect to center
    bar_offset = []
    mid_point = (len(group_list) * bar_width) / 2
    for i in range(len(group_list)):
        bar_offset.append(bar_width * i + 0.5 * bar_width - mid_point)

    x_axis = np.arange(len(x_ticks))
    # draw figure by column
    for (index, group_name) in zip(range(len(group_list)), group_list):
        y = y_values[group_name]
        yerr = None
        if std_dev:
            yerr = std_dev[group_name]
        bar_pos = x_axis + bar_offset[index]

        plt.bar(bar_pos,
                y,
                width=bar_width,
                label=legend_label[group_name],
                yerr=yerr,
                color=get_next_color())

        # print data label
        for (x, y) in zip(bar_pos, y):
            text = '{:.0f}'.format(y)
            plt.text(
                x,
                y,
                text,
                size=datalabel_size,
                ha='center',
                va=
                datalabel_va,  # 'bottom', 'baseline', 'center', 'center_baseline', 'top'
            )

    # Legend: Change the ncol and loc to fine-tune the location of legend
    # if legend_label != None:
    #     plt.legend(fontsize=legend_font_size, loc='lower left', ncol=2)
    #     # plt.legend(fontsize=legend_font_size,
    #     #            ncol=2,
    #     #            loc='upper left',
    #     #            bbox_to_anchor=(0, 1.2),
    #     #            columnspacing=0.3)

    plt.savefig(fig_save_path, bbox_inches='tight')

reset_color()
# r256-w256 read thr
if True:
    y_values = r_thr_r256_w256
    std_dev = None
    legend_label = {i: i for i in group_list}
    title = None
    xlabel = None
    ylabel = 'Throughput~(K IOPS)'
    fig_save_path = 'samsung-r-thr-r256-w256.pdf'
    # plot
    fig, ax = plt.subplots(figsize=(12, 8))
    plt.grid(axis='y')  # x, y, both

    # x, y axis limit
    # ax.set_xlim(0, 2)
    ax.set_ylim(0, 265)

    # set ticks
    plt.xticks(list(np.arange(len(x_ticks))), x_ticks)

    if title:
        plt.title(title)

    if xlabel:
        plt.xlabel(xlabel, fontsize=axis_label_font_size)
    if ylabel:
        plt.ylabel(ylabel, fontsize=axis_label_font_size)

    ax.tick_params(axis='both', which='major', labelsize=axis_tick_font_size)

    # compute bar offset, with respect to center
    bar_offset = []
    mid_point = (len(group_list) * bar_width) / 2
    for i in range(len(group_list)):
        bar_offset.append(bar_width * i + 0.5 * bar_width - mid_point)

    x_axis = np.arange(len(x_ticks))
    # draw figure by column
    for (index, group_name) in zip(range(len(group_list)), group_list):
        y = y_values[group_name]
        yerr = None
        if std_dev:
            yerr = std_dev[group_name]
        bar_pos = x_axis + bar_offset[index]

        plt.bar(bar_pos,
                y,
                width=bar_width,
                label=legend_label[group_name],
                yerr=yerr,
                color=get_next_color())

        # print data label
        for (x, y) in zip(bar_pos, y):
            text = '{:.0f}'.format(y)
            plt.text(
                x,
                y,
                text,
                size=datalabel_size,
                ha='center',
                va=
                datalabel_va,  # 'bottom', 'baseline', 'center', 'center_baseline', 'top'
            )

    # Legend: Change the ncol and loc to fine-tune the location of legend
    # if legend_label != None:
    #     plt.legend(fontsize=legend_font_size, loc='lower left', ncol=2)
    #     # plt.legend(fontsize=legend_font_size,
    #     #            ncol=2,
    #     #            loc='upper left',
    #     #            bbox_to_anchor=(0, 1.2),
    #     #            columnspacing=0.3)

    plt.savefig(fig_save_path, bbox_inches='tight')

reset_color()
# r256-w256 write thr
if True:
    y_values = w_thr_r256_w256
    std_dev = None
    legend_label = {i: i for i in group_list}
    title = None
    xlabel = None
    ylabel = 'Throughput~(K IOPS)'
    fig_save_path = 'samsung-w-thr-r256-w256.pdf'
    # plot
    fig, ax = plt.subplots(figsize=(12, 8))
    plt.grid(axis='y')  # x, y, both

    # x, y axis limit
    # ax.set_xlim(0, 2)
    ax.set_ylim(0, 265)

    # set ticks
    plt.xticks(list(np.arange(len(x_ticks))), x_ticks)

    if title:
        plt.title(title)

    if xlabel:
        plt.xlabel(xlabel, fontsize=axis_label_font_size)
    if ylabel:
        plt.ylabel(ylabel, fontsize=axis_label_font_size)

    ax.tick_params(axis='both', which='major', labelsize=axis_tick_font_size)

    # compute bar offset, with respect to center
    bar_offset = []
    mid_point = (len(group_list) * bar_width) / 2
    for i in range(len(group_list)):
        bar_offset.append(bar_width * i + 0.5 * bar_width - mid_point)

    x_axis = np.arange(len(x_ticks))
    # draw figure by column
    for (index, group_name) in zip(range(len(group_list)), group_list):
        y = y_values[group_name]
        yerr = None
        if std_dev:
            yerr = std_dev[group_name]
        bar_pos = x_axis + bar_offset[index]

        plt.bar(bar_pos,
                y,
                width=bar_width,
                label=legend_label[group_name],
                yerr=yerr,
                color=get_next_color())

        # print data label
        for (x, y) in zip(bar_pos, y):
            text = '{:.0f}'.format(y)
            plt.text(
                x,
                y,
                text,
                size=datalabel_size,
                ha='center',
                va=
                datalabel_va,  # 'bottom', 'baseline', 'center', 'center_baseline', 'top'
            )

    # Legend: Change the ncol and loc to fine-tune the location of legend
    if legend_label != None:
        plt.legend(fontsize=legend_font_size, loc='upper left', ncol=2)
        # plt.legend(fontsize=legend_font_size,
        #            ncol=2,
        #            loc='upper left',
        #            bbox_to_anchor=(0, 1.2),
        #            columnspacing=0.3)

    plt.savefig(fig_save_path, bbox_inches='tight')