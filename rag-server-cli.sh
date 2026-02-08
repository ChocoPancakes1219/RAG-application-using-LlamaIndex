#!/bin/bash
# RAG Server CLI wrapper

case "$1" in
  start)
    sudo systemctl start rag-server
    ;;
  stop)
    sudo systemctl stop rag-server
    ;;
  restart)
    sudo systemctl restart rag-server
    ;;
  status)
    sudo systemctl status rag-server
    ;;
  logs)
    sudo journalctl -u rag-server -f
    ;;
  enable)
    sudo systemctl enable rag-server
    ;;
  disable)
    sudo systemctl disable rag-server
    ;;
  *)
    echo "Usage: rag-server {start|stop|restart|status|logs|enable|disable}"
    exit 1
    ;;
esac
