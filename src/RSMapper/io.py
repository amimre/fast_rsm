"""
This module contains tools used for parsing data/metadata files.
"""

# Because of the dumb way that values are stored in the nexusformat package.
# pylint: disable=protected-access

import os
from typing import Union, Tuple, List
from pathlib import Path

import nexusformat.nexus as nx

from .image import Image
from .metadata import Metadata
from .motors import Motors


def i07_nexus_parser(path_to_nx: Union[str, Path], beam_centre: Tuple[int]) -> \
        Tuple[List['Image'], 'Metadata']:
    """
    Parses an I07 nexus file. Returns everything required to instantiate a Scan.

    Args:
        path_to_nx:
            Path to the nexus file to parse.
        beam_centre:
            The beam centre when all axes are zeroed.

    Returns:
        A tuple taking the form (list_of_images, metadata). This can be used to
        instantiate a Scan.
    """
    nx_file = nx.nxload(path_to_nx)
    # Just use some hard-coded paths to grab the data.
    # It doesn't need to be pretty; it needs to work.
    detector_distance = nx_file["/entry/instrument/diff1detdist/value"]._value
    energy = nx_file["/entry/instrument/dcm1energy/value"]._value

    default = str(nx_file["/entry/"].get_default())
    image_path = nx_file[
        f"/entry/instrument/{default}/data_file/file_name"]._value

    # Now we need to do some detector specific stuff.
    if 'pil' in default:
        # It's the pilatus detector.
        pixel_size = 172e-6
        data_shape = [1475, 1679]
        metadata = Metadata(nx_file, "i07", detector_distance, pixel_size,
                            energy, data_shape, beam_centre)
        motors = Motors(metadata)

        # Search for images (usually necessary outside of Diamond).
        # First make sure everything is a string (could be bytes).
        image_path = [bytes.decode(x, 'utf-8') for x in image_path]
        image_paths = _try_to_find_files(image_path, [path_to_nx])
        images = [Image.from_file(x, motors, metadata) for x in image_paths]
    else:
        # It's the excalibur detector.
        raise NotImplementedError()

    return images, Metadata(nx_file, "i07", detector_distance, pixel_size,
                            energy, data_shape, beam_centre)


def _try_to_find_files(filenames: List[str],
                       additional_search_paths: List[str]):
    """
    Check that data files exist if the file parsed by parser pointed to a
    separate file containing intensity information. If the intensity data
    file could not be found in its original location, check a series of
    probable locations for the data file.

    Returns:
        `list` of `str`:
            List of the corrected, actual paths to the files.
    """
    found_files = []

    # If we had only one file, make a list out of it.
    if not hasattr(filenames, "__iter__"):
        filenames = [filenames]

    cwd = os.getcwd()
    start_dirs = [
        cwd,  # maybe file is stored near the current working dir
        # To search additional directories, add them in here manually.
    ]
    start_dirs.extend(additional_search_paths)

    local_start_directories = [x.replace('\\', '/') for x in start_dirs]
    num_start_directories = len(local_start_directories)

    # Now extend the additional search paths.
    for i in range(num_start_directories):
        search_path = local_start_directories[i]
        split_srch_path = search_path.split('/')
        for j in range(len(split_srch_path)):
            extra_path_list = split_srch_path[:-(j+1)]
            extra_path = '/'.join(extra_path_list)
            local_start_directories.append(extra_path)

    # This line allows for a loading bar to show as we check the file.
    for i, _ in enumerate(filenames):
        # Better to be safe... Note: windows is happy with / even though it
        # defaults to \
        filenames[i] = str(filenames[i]).replace('\\', '/')

        # Maybe we can see the file in its original storage location?
        if os.path.isfile(filenames[i]):
            found_files.append(filenames[i])
            continue

        # If not, maybe it's stored locally? If the file was stored at
        # location /a1/a2/.../aN/file originally, for a local directory LD,
        # check locations LD/aj/aj+1/.../aN for all j<N and all LD's of
        # interest. This algorithm is a generalization of Andrew McCluskey's
        # original approach.

        # now generate a list of all directories that we'd like to check
        candidate_paths = []
        split_file_path = str(filenames[i]).split('/')
        for j in range(len(split_file_path)):
            local_guess = '/'.join(split_file_path[j:])
            for start_dir in local_start_directories:
                candidate_paths.append(
                    os.path.join(start_dir, local_guess))

        # Iterate over each of the candidate paths to see if any of them contain
        # the data file we're looking for.
        found_file = False
        for candidate_path in candidate_paths:
            if os.path.isfile(candidate_path):
                # File found - add the correct file location to found_files
                found_files.append(candidate_path)
                found_file = not found_file
                print("Data file found at " + candidate_path + ".")
                break

        # If we didn't find the file, tell the user.
        if not found_file:
            raise FileNotFoundError(
                "The data file with the name " + filenames[i] + " could "
                "not be found. The following paths were searched:\n" +
                "\n".join(candidate_paths)
            )
    return found_files
