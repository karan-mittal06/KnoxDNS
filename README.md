# KnoxDNS

KnoxDNS is a secure and privacy-focused DNS resolver that supports DNS-over-HTTPS (DoH). It includes a website for easy management and an AI-powered malicious URL checker to enhance security. KnoxDNS aims to provide a seamless, high-performance, and user-friendly DNS experience, ensuring that users can browse the internet without concerns over data privacy, tracking, or malicious threats.

With KnoxDNS, users can take control of their DNS queries and safeguard their online activities. By leveraging encryption and AI-driven security measures, KnoxDNS effectively mitigates threats like DNS hijacking, phishing attacks, and unauthorized tracking.

## Features

- X **DNS-over-HTTPS (DoH)**: Encrypts DNS queries for enhanced privacy.
- X **High Performance**: Optimized for low latency and fast responses.
- X **Security Focused**: Prevents DNS spoofing and improves user protection.
- X **AI threat detection and protection**: Live AI threat detection tool to protect against malicious urls
- X **Analytics**: Real-time analytics available for flagged sites

## Installation

### Prerequisites

- Python 3.9
- pip

### Steps

1. Clone the repository:
   ```sh
   git clone https://github.com/karan-mittal06/knoxdns.git
   cd knoxdns
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Run the server:
   ```sh
   python main.py
   ```

## Usage

### API Endpoint

Send a DNS query using DoH:

```sh
curl -X GET "http://localhost:8080/dns-query?name=example.com&type=A"
```

### Integration with System

To use KnoxDNS as your system resolver, configure your network settings to point to your KnoxDNS server.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.


