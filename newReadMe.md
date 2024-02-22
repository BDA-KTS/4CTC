# 4TCT: A 4chan Text Collection Tool

## Description
4TCT is a specialized tool designed for the efficient collection of textual data from the 4chan platform. It automates the process of gathering posts from various boards, aiming to facilitate research and analysis in social science and computational linguistics.

This tool is particularly useful for analyzing online discourse, community dynamics, and trends within the 4chan ecosystem. It can support studies on topics like meme culture, information dissemination, and the impact of anonymous social media on public opinion.

## Social Science usecase(s)
A team of social scientists is conducting a research project to explore online communities' influence on language evolution and cultural trends. They decide to focus on 4chan, known for its anonymous and varied user base, to capture authentic and unfiltered expressions. The 4chan Data Collection Tool becomes an essential component in their data acquisition strategy.

## Structure
- The tool's architecture includes a `src/` directory for core scripts, with `requester.py` handling data collection, `board.py` managing board-specific requests, and `utils.py` for auxiliary functions. Data is stored in a `data/` directory created upon initiation, and documentation is available in `docs/`.

Setup
## Environment Setup
- Requires Python 3.10.2 or 3.11.4. Suitable for environments focused on data collection and analysis.
- Dependencies are listed in `requirements.txt` and can be installed via `pip install -r requirements.txt` to ensure the tool functions correctly.


## Input Data (DBD datasets)
- Not applicable as 4TCT gathers data directly from 4chan. 

## Sample Input and Output Data
- Input data is not applicable as the tool dynamically collects live data from 4chan boards based on user-defined parameters.
- Outputs include `.json` files containing collected posts, structured according to 4chan's API documentation, with directories organized by date and board.

## How to Use
- Run `python src/requester.py` to start data collection, with options `-b` for board selection and `-e` for board exclusion. Advanced usage includes adjusting request intervals and logging levels for detailed monitoring.

## Contact Details
- For questions or contributions, contact Jack H. Culbert at jack.culbert@gesis.org and Po-Chun Chang for maintenance issues at po-chun.chang@gesis.org.

## Publication (Optional)
- The associated technical report is available at [arXiv:2307.03556](https://arxiv.org/abs/2307.03556). Users are encouraged to cite this paper when using the tool in research.

## Acknowledgements (if any)
- Gratitude is extended to the 4chan API team for providing the foundational resources that facilitate this tool's functionality.

## Disclaimer (Optional)
- The creators of 4TCT and GESIS are not affiliated with 4chan. The tool is intended for academic research, and users are responsible for ensuring the legality and ethicality of their data use.
