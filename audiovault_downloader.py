import os
import subprocess
import pandas as pd
import shutil
import requests  # Add this import
from bs4 import BeautifulSoup  # Ensure this is also imported



def fetch_results(search_term):
    """
    Fetches search results for the given term from the website.
    Parses the table and extracts relevant information.
    """
    print(f"Starting search for '{search_term}'...")
    base_url = "https://audiovault.net/shows"
    params = {'search': search_term}

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching results for '{search_term}': {e}")
        return []

    print(f"Parsing results for '{search_term}'...")
    soup = BeautifulSoup(response.text, 'html.parser')

    table_body = soup.find('table')
    if not table_body:
        print(f"No table found on the results page for '{search_term}'.")
        return []
    table_body = table_body.find('tbody')
    if not table_body:
        print(f"No results found in the table for '{search_term}'.")
        return []

    results = []
    for row in table_body.find_all('tr'):
        columns = row.find_all('td')
        if len(columns) < 3:
            continue

        id_ = columns[0].text.strip()
        name = columns[1].text.strip()
        download_link = columns[2].find('a')['href']

        results.append({
            'Search Term': search_term,
            'ID': id_,
            'Name': name,
            'Download Link': download_link,
            'Download': False  # Default to False
        })

    print(f"Found {len(results)} results for '{search_term}'.")
    return results


def fetch_file_metadata(download_url, cookies_file):
    """
    Fetches file metadata using curl and cookies.txt.
    """
    try:
        result = subprocess.run(
            ['curl', '-I', '-b', cookies_file, download_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        headers = result.stdout.splitlines()

        metadata = {}
        for line in headers:
            if line.lower().startswith("content-length"):
                metadata['Content-Length'] = int(line.split(': ')[1].strip())  # In bytes
            elif line.lower().startswith("content-type"):
                metadata['Content-Type'] = line.split(': ')[1].strip()
            elif line.lower().startswith("last-modified"):
                metadata['Last-Modified'] = line.split(': ', 1)[1].strip()
            elif line.lower().startswith("content-disposition"):
                if 'filename=' in line:
                    metadata['Filename'] = line.split('filename=')[1].strip('"')

        return metadata
    except Exception as e:
        print(f"Error fetching metadata for {download_url}: {e}")
        return {}


def display_progress(term, term_index, term_total, file_index, file_total, overall_progress):
    """
    Displays progress for metadata fetching with overwriting row behavior.
    """
    columns = shutil.get_terminal_size((80, 20)).columns
    progress_bar_length = columns - 50
    completed = int(progress_bar_length * overall_progress)
    progress_bar = f"[{'#' * completed}{'.' * (progress_bar_length - completed)}]"

    progress_message = f"Fetching metadata for {term} ({file_index}/{file_total}) - {int(overall_progress * 100)}% {progress_bar}"
    print(progress_message.ljust(columns), end='\r')


def add_metadata_to_dataframe(df, cookies_file):
    """
    Adds file metadata to the DataFrame for each download link with a progress bar.
    """
    print("\nFetching metadata for each file...\n")
    total_files = len(df)
    current_file = 0

    metadata_list = []

    for term_index, (term, group) in enumerate(df.groupby('Search Term'), start=1):
        term_total = len(group)

        for file_index, row in enumerate(group.itertuples(), start=1):
            current_file += 1
            overall_progress = current_file / total_files
            display_progress(term, term_index, len(df['Search Term'].unique()), file_index, term_total, overall_progress)

            metadata = fetch_file_metadata(row._4, cookies_file)  # _4 is "Download Link"
            metadata_list.append(metadata)

    print("\n")  # Newline after progress bar
    metadata_df = pd.DataFrame(metadata_list)
    df = pd.concat([df.reset_index(drop=True), metadata_df.reset_index(drop=True)], axis=1)
    return df


def review_and_mark(df):
    """
    Allows the user to review and mark items for download based on user input.
    """
    for term in df['Search Term'].unique():
        print(f"\nWhat would you like to do with items for '{term}'?")

        # Display relevant details
        term_items = df[df['Search Term'] == term][['Show Item ID', 'Name', 'Content-Length']]
        term_items['Size (MB)'] = (term_items['Content-Length'] / (1024 ** 2)).round(2)
        print(term_items[['Show Item ID', 'Name', 'Size (MB)']].to_string(index=False))
        print()

        print("1. All")
        print("2. None")
        print("3. IDs (inclusive)")
        print("4. IDs (exclusive)")
        print("5. Search term (inclusive)")
        print("6. Search term (exclusive)")

        choice = input("Enter your choice (1-6): ").strip()

        if choice == '1':  # All
            df.loc[df['Search Term'] == term, 'Download'] = True
        elif choice == '2':  # None
            df.loc[df['Search Term'] == term, 'Download'] = False
        elif choice == '3':  # IDs (inclusive)
            include_ids = input("Enter the Show Item IDs to include (comma-separated): ").strip()
            include_ids = [int(x) for x in include_ids.split(',')]
            df.loc[(df['Search Term'] == term) & (df['Show Item ID'].isin(include_ids)), 'Download'] = True
            df.loc[(df['Search Term'] == term) & (~df['Show Item ID'].isin(include_ids)), 'Download'] = False
        elif choice == '4':  # IDs (exclusive)
            exclude_ids = input("Enter the Show Item IDs to exclude (comma-separated): ").strip()
            exclude_ids = [int(x) for x in exclude_ids.split(',')]
            df.loc[(df['Search Term'] == term) & (df['Show Item ID'].isin(exclude_ids)), 'Download'] = False
            df.loc[(df['Search Term'] == term) & (~df['Show Item ID'].isin(exclude_ids)), 'Download'] = True
        elif choice == '5':  # Search term (inclusive)
            keyword = input("Enter the keyword to include: ").strip().lower()
            df.loc[(df['Search Term'] == term) & (df['Name'].str.lower().str.contains(keyword)), 'Download'] = True
            df.loc[(df['Search Term'] == term) & (~df['Name'].str.lower().str.contains(keyword)), 'Download'] = False
        elif choice == '6':  # Search term (exclusive)
            keyword = input("Enter the keyword to exclude: ").strip().lower()
            df.loc[(df['Search Term'] == term) & (~df['Name'].str.lower().str.contains(keyword)), 'Download'] = True
            df.loc[(df['Search Term'] == term) & (df['Name'].str.lower().str.contains(keyword)), 'Download'] = False
        else:
            print("Invalid choice, skipping this term.")

    return df



def download_files_with_progress(df, cookies_file, output_csv):
    """
    Downloads files marked for download with a progress bar and updates the DataFrame with download status.
    """
    df['Downloaded'] = "not started"  # Initialize download status

    for index, row in df[df['Download']].iterrows():
        search_term = row['Search Term']
        download_url = row['Download Link']
        filename = row['Filename']
        
        # Create the directory structure: download/search_term/
        folder = os.path.join(os.getcwd(), "download", search_term)
        os.makedirs(folder, exist_ok=True)
        
        # Full file path: download/search_term/filename
        file_path = os.path.join(folder, filename)

        # Skip downloading if the file already exists
        if os.path.exists(file_path):
            print(f"\nFile already exists: {file_path}. Skipping download.")
            df.at[index, 'Downloaded'] = "skipped"
            continue

        print(f"\nDownloading {filename} to {folder}...")

        try:
            # Use curl to download the file with a progress bar
            result = subprocess.run(
                ['curl', '-b', cookies_file, '-o', file_path, '--progress-bar', download_url],
                stderr=subprocess.STDOUT,
                text=True
            )
            if result.returncode == 0:
                df.at[index, 'Downloaded'] = "success"
                print(f"\nDownloaded {filename} successfully.")
            else:
                df.at[index, 'Downloaded'] = "fail"
                print(f"\nFailed to download {filename}.")
        except Exception as e:
            df.at[index, 'Downloaded'] = "incomplete"
            print(f"\nError downloading {filename}: {e}")

        # Save the updated DataFrame to CSV after each file
        df.to_csv(output_csv, index=False)

    return df




def calculate_total_size(df):
    """
    Calculates the total size of files marked for download.
    """
    total_size = df.loc[df['Download'], 'Content-Length'].sum() / (1024 ** 2)
    print(f"\nTotal size of selected files for download: {total_size:.2f} MB")


def main():
    """
    Main function to handle search, metadata fetching, download, and CSV updates.
    """
    print("Welcome to the Audiovault Downloader Script!")
    print("Enter search terms separated by commas (e.g., show name, supershow):")

    # Get search terms from the user
    search_terms = input("Search terms: ").strip().split(',')
    search_terms = [term.strip() for term in search_terms if term.strip()]

    # Initialize a list to store all results
    all_results = []

    # Fetch results for each search term
    for term in search_terms:
        results = fetch_results(term)
        all_results.extend(results)

    # Proceed only if results were found
    if all_results:
        # Create a DataFrame from the fetched results
        df = pd.DataFrame(all_results)
        df['Show Item ID'] = df.groupby('Search Term').cumcount() + 1

        # Add metadata to the DataFrame
        cookies_file = "cookies.txt"  # Ensure this file exists in the project root
        df = add_metadata_to_dataframe(df, cookies_file)

        # Review and mark files for download
        df = review_and_mark(df)

        # Save the DataFrame to a CSV after the selection step
        output_csv = "search_results_with_metadata.csv"
        df.to_csv(output_csv, index=False)
        print(f"\nResults saved to '{output_csv}'.")

        # Check if any files are marked for download
        if df['Download'].any():
            # Proceed to download marked files
            df = download_files_with_progress(df, cookies_file, output_csv)
        else:
            # Notify the user if no files were marked for download
            print("\nNo files were marked for download. Skipping download step.")
    else:
        print("No results found for any of the search terms.")

    # Final message
    print("\nScript execution completed.")



if __name__ == "__main__":
    main()
