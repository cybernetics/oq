# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2019 Manas.Tech
# License granted by Canonical Limited
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""The Crystal plugin can be used for Crystal projects using `shards`.

This plugin uses the common plugin keywords as well as those for "sources".
For more information check the 'plugins' topic for the former and the
'sources' topic for the latter.

Additionally, this plugin uses the following plugin-specific keywords:

    - crystal-channel:
      (string, default: latest/stable)
      The Snap Store channel to install Crystal from.
"""

import os
import shutil

import snapcraft
from snapcraft import file_utils
from snapcraft.internal import common, elf, errors

_CRYSTAL_CHANNEL = "latest/stable"


class CrystalPlugin(snapcraft.BasePlugin):
    @classmethod
    def schema(cls):
        schema = super().schema()

        schema["properties"]["crystal-channel"] = {
            "type": "string",
            "default": _CRYSTAL_CHANNEL,
        }
        schema["required"] = ["source"]

        return schema

    @classmethod
    def get_pull_properties(cls):
        return ["crystal-channel"]

    def __init__(self, name, options, project):
        super().__init__(name, options, project)

        if project.info.base not in ("core", "core16", "core18"):
            raise errors.PluginBaseError(part_name=self.name, base=project.info.base)

        self.build_snaps.append("crystal/{}".format(self.options.crystal_channel))
        self.build_packages.extend(
            [
                "gcc",
                "pkg-config",
                "libpcre3-dev",
                "libevent-dev",
                "libyaml-dev",
                "libgmp-dev",
                "libxml2-dev",
            ]
        )

    def build(self):
        super().build()

        self.run(["shards", "install", "--production"], self.builddir)
        self.run(["shards", "build", "--production"], self.builddir)

        output_bin = os.path.join(self.builddir, "bin")
        if not os.path.exists(output_bin):
            raise errors.SnapcraftEnvironmentError(
                "No binaries were built. Ensure the shards.yaml contains valid targets."
            )

        install_bin_path = os.path.join(self.installdir, "bin")

        bin_paths = (os.path.join(output_bin, b) for b in os.listdir(output_bin))
        elf_files = (elf.ElfFile(path=b) for b in bin_paths if elf.ElfFile.is_elf(b))

        os.makedirs(install_bin_path, exist_ok=True)

        for elf_file in elf_files:
            shutil.copy2(
                elf_file.path,
                os.path.join(install_bin_path, os.path.basename(elf_file.path)),
            )

            elf_dependencies_path = elf_file.load_dependencies(
                root_path=self.installdir,
                core_base_path=common.get_core_path(self.project.info.base),
            )
            for elf_dependency_path in elf_dependencies_path:
                lib_install_path = os.path.join(
                    self.installdir, elf_dependency_path[1:]
                )
                os.makedirs(os.path.dirname(lib_install_path), exist_ok=True)
                if not os.path.exists(lib_install_path):
                    file_utils.link_or_copy(
                        elf_dependency_path, lib_install_path, follow_symlinks=True
                    )