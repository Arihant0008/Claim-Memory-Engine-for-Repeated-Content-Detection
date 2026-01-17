"""
CLI entry point for PCM system.
Provides command-line interface for common operations.
"""

import argparse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))


def cmd_ingest(args):
    """Run data ingestion."""
    from src.data_ingestion import ingest_all_datasets
    
    print("🚀 Starting data ingestion...")
    result = ingest_all_datasets(use_real_datasets=args.real_datasets)
    print(f"\n✅ Done! Ingested {result['success_count']} claims.")


def cmd_verify(args):
    """Verify a single claim."""
    from src.pipeline import ClaimVerificationPipeline
    
    pipeline = ClaimVerificationPipeline()
    result = pipeline.verify(text=args.claim)
    
    v = result.get("verification", {})
    m = result.get("memory", {})
    
    print(f"\n📋 Claim: {args.claim}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🎯 Verdict: {v.get('verdict', 'Unknown')}")
    print(f"📊 Confidence: {v.get('confidence', 0):.0%}")
    print(f"💬 Explanation: {v.get('explanation', 'N/A')}")
    print(f"💾 Memory: {m.get('message', 'N/A')}")
    
    if args.verbose:
        print(f"\n📚 Evidence:")
        for i, ev in enumerate(result.get("evidence", [])[:3]):
            print(f"   {i+1}. {ev.get('claim_text', '')[:60]}...")
            print(f"      Verdict: {ev.get('verdict')} | Similarity: {ev.get('similarity_score', 0):.2f}")


def cmd_stats(args):
    """Show collection statistics."""
    from src.agents.memory import MemoryUpdateAgent
    
    agent = MemoryUpdateAgent()
    stats = agent.retriever.get_collection_stats()
    
    print("\n📊 Collection Statistics")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Total Claims: {stats.get('total_claims', 'N/A')}")
    print(f"Indexed Vectors: {stats.get('indexed_vectors', 'N/A')}")
    print(f"Status: {stats.get('status', 'N/A')}")
    
    print("\n🏆 Top 5 Most Verified Claims:")
    top_claims = agent.get_top_claims(limit=5)
    for i, claim in enumerate(top_claims):
        emoji = "✅" if claim.get("verdict") == "True" else "❌" if claim.get("verdict") == "False" else "❓"
        print(f"   {i+1}. {emoji} {claim.get('claim_text', '')[:50]}... (seen {claim.get('seen_count', 0)}x)")


def cmd_clear(args):
    """Clear the collection (use with caution!)."""
    from src.agents.memory import MemoryUpdateAgent
    
    if not args.force:
        confirm = input("⚠️  This will DELETE all claims. Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
    
    agent = MemoryUpdateAgent()
    success = agent.clear_collection()
    
    if success:
        print("✅ Collection cleared and recreated.")
    else:
        print("❌ Failed to clear collection.")


def main():
    parser = argparse.ArgumentParser(
        description="Persistent Claim Memory - Misinformation Detection CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py ingest                  # Load claims into database
  python cli.py verify "claim text"     # Verify a claim
  python cli.py stats                   # Show collection stats
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest claims into database")
    ingest_parser.add_argument(
        "--real-datasets", "-r",
        action="store_true",
        default=True,
        help="Use real HuggingFace datasets (default: True)"
    )
    ingest_parser.add_argument(
        "--curated-only", "-c",
        action="store_true",
        help="Use only curated fallback claims"
    )
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a claim")
    verify_parser.add_argument("claim", type=str, help="The claim to verify")
    verify_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed evidence"
    )
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show collection statistics")
    
    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear the collection")
    clear_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation"
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    # Route to command handler
    commands = {
        "ingest": cmd_ingest,
        "verify": cmd_verify,
        "stats": cmd_stats,
        "clear": cmd_clear
    }
    
    # Handle curated-only flag
    if hasattr(args, 'curated_only') and args.curated_only:
        args.real_datasets = False
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
