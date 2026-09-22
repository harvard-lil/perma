![](https://raw.githubusercontent.com/harvard-lil/perma/main/perma_web/static/img/watermark.png)

Perma - indelible links
=====

Perma.cc helps authors and journals create permanent archived citations in their published work.

[![test status](https://github.com/harvard-lil/perma/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/harvard-lil/perma/actions)
[![codecov](https://codecov.io/gh/harvard-lil/perma/branch/main/graph/badge.svg?token=PmUtgx6QFh)](https://codecov.io/gh/harvard-lil/perma)

## Connect with Perma.cc

- Use Perma.cc at [Perma.cc](https://perma.cc)
- Email us at [info@perma.cc](mailto:info@perma.cc)

## Installation

If you're installing Perma.cc, see [the installation section of the developer doc](https://github.com/harvard-lil/perma/blob/main/developer.md#installing-perma).

## Developing in Perma.cc

If you're wrenchin' on Perma.cc, see [the developer doc](https://github.com/harvard-lil/perma/blob/main/developer.md).

## Contributing and releases

Open feature and fix PRs against **`main`**, the default integration branch.
`develop` is retained as a frozen historical branch; existing PRs targeting it
will be moved in coordination with their authors.

Releases use merge-commit promotions from `main` to `staging`, then from
`staging` to `prod`. Merging a promotion deploys that environment; production
uses the image already validated on staging. See [the release workflow](developer.md#git-and-github).

## License

Dual licensed under the MIT license (below) and [GPL license](http://www.gnu.org/licenses/gpl-3.0.html).

<small>
MIT License

Copyright (c) 2021 The Harvard Library Innovation Lab

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
</small>
