#include <pcap/pcap.h>

#include <cstdint>
#include <iomanip>
#include <iostream>
#include <string>

#include "udp.h"
#include "cbe.h"
#include "snapshotRefresh.h"
#include "orderbook.h"

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "usage: reference_snapshot_dump <pcap>\n";
        return 2;
    }

    char errbuf[PCAP_ERRBUF_SIZE];
    pcap_t* handle = pcap_open_offline(argv[1], errbuf);
    if (handle == nullptr) {
        std::cerr << "pcap_open_offline failed: " << errbuf << "\n";
        return 2;
    }

    OrderBookCollection orderbooks;
    const u_char* packet = nullptr;
    struct pcap_pkthdr header;
    while ((packet = pcap_next(handle, &header)) != nullptr) {
        if (header.caplen < 42) {
            continue;
        }
        UDP udp(packet + 34);
        if (udp.src_port == 319 || udp.src_port == 320) {
            continue;
        }
        CBE cbe(udp.payload, udp.payload_length);
        for (const Message& msg : cbe.messages) {
            if (msg.template_id == 52) {
                SnapShotFullRefresh snapshot(msg.payload);
                orderbooks.updateOrderBook(snapshot, cbe.header.sendtime);
            }
        }
    }
    pcap_close(handle);

    std::cout << "security_id,side,level,price,size,num_orders\n";
    for (const auto& [security_id, book] : orderbooks.collection) {
        for (const auto& [level, entry] : book.bids) {
            std::cout << security_id << ",bid," << level << ","
                      << std::fixed << std::setprecision(0) << entry.price << ","
                      << entry.quantity << "," << entry.order_count << "\n";
        }
        for (const auto& [level, entry] : book.asks) {
            std::cout << security_id << ",ask," << level << ","
                      << std::fixed << std::setprecision(0) << entry.price << ","
                      << entry.quantity << "," << entry.order_count << "\n";
        }
    }
    return 0;
}
