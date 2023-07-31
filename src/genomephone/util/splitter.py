import pysam

from genomephonepy.data.resolution import Resolution


def split_bam(bam_file, output_dir):
    """
    Split a BAM file into multiple BAM files, one per chromosome.

    :param bam_file: Input BAM file
    :param output_dir: Output directory
    :return: List of BAM files
    """
    bam_files = []
    with pysam.AlignmentFile(bam_file, "rb") as samfile:
        for chromosome in samfile.references:
            bam_file = f"{output_dir}/{chromosome}.bam"
            bam_files.append(bam_file)
            with pysam.AlignmentFile(bam_file, "wb", template=samfile) as out:
                for read in samfile.fetch(chromosome):
                    out.write(read)
    return bam_files
