import subprocess
import json
import sys
import os

def get_protocols_from_pcap(pcap_file):
    if not os.path.exists(pcap_file):
        print(f"Error: File not found at '{pcap_file}'", file=sys.stderr)
        return None

    command = [
        'tshark',
        '-r', pcap_file,
        '-T', 'fields',
        '-e', 'frame.protocols'
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        unique_protocols = set()
        output = result.stdout.strip()
        
        if not output:
            return []

        for line in output.splitlines():
            protocols_in_frame = line.strip().split(':')
            for proto in protocols_in_frame:
                if proto:  
                    unique_protocols.add(proto)
        
        return sorted(list(unique_protocols))
        
    except subprocess.CalledProcessError as e:
        print(f"Error analyzing file {pcap_file}: {e.stderr}", file=sys.stderr)
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_pcap_file>")
        sys.exit(1)
        
    pcap_path = sys.argv[1]
    protocols = get_protocols_from_pcap(pcap_path)
    
    if protocols is not None:
        print(json.dumps({
            "file": os.path.basename(pcap_path),
            "protocols": protocols
        }, indent=2))
