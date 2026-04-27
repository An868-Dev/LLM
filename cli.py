import sys
import logging
from LLM.settings import settings
from LLM.supervisor import Supervisor
from LLM.knowledge import HR_KNOWLEDGE_BASE

logging.basicConfig(level=logging.INFO)

def main():
    print("""Gõ 'exit' để thoát | 'reset' để bắt đầu hội thoại mới""")

    try:
        settings.validate()
    except ValueError as e:
        sys.exit(1)

    print("⏳ Khởi động hệ thống...")
    supervisor = Supervisor()

    stats = supervisor.vector_store.get_stats()
    if stats["total_documents"] == 0:
        print(f"Nạp {len(HR_KNOWLEDGE_BASE)} tài liệu HR vào VectorDB...")
        supervisor.vector_store.ingest_documents(HR_KNOWLEDGE_BASE)

    print(f"{supervisor.vector_store.get_stats()['total_documents']} tài liệu\n")

    # Chat loop
    while True:
        try:
            user_input = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nKết thúc phiên làm việc. Tạm biệt!")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Kết thúc")
            break

        if user_input.lower() == "reset":
            supervisor.reset_conversation()
            print("reset")
            continue

        if user_input.lower() == "status":
            status = supervisor.get_system_status()
            print(f"📊 Status: {status}\n")
            continue

        print("\nCHRO suy nghĩ\n")
        state = supervisor.run(user_input)

        print(f"CHRO [{state.router_output.intent if state.router_output else 'N/A'}]:")
        print(state.final_response)
        if state.rag_results:
            print(f"\nNguồn tham khảo: {len(state.rag_results)} tài liệu từ Knowledge Base")
if __name__ == "__main__":
    main()