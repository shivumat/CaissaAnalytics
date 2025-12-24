"""
Demo script showing how to use the CaissaAnalytics API
"""
import asyncio
import httpx


async def main():
    # Sample PGN with a game containing potential mistakes
    sample_pgn = """[Event "Casual Game"]
[Site "Local"]
[Date "2024.12.24"]
[Round "?"]
[White "Player A"]
[Black "Player B"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 
6. Re1 b5 7. Bb3 O-O 8. c3 d6 9. h3 Na5 10. Bc2 c5 
11. d4 Qc7 12. Nbd2 cxd4 13. cxd4 Nc6 14. Nb3 a5 
15. Be3 a4 16. Nbd2 Bd7 17. Rc1 Qb7 18. dxe5 dxe5 
19. Nh4 g6 20. Nhf3 Rfd8 21. Qe2 Be6 22. Red1 h6 
23. Bb1 Rac8 24. Ba2 Bxa2 25. Qxa2 Kg7 26. Qe2 Rxd2 
27. Rxd2 Rd8 28. Rcd1 Rxd2 29. Rxd2 Qc7 30. Rd5 Qc4 
31. Qd2 Nxd5 32. exd5 Nd8 33. Qd3 Qxd3 34. cxd3 Nf7 1-0"""

    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 1. Check if server is running
        print("1. Checking server health...")
        response = await client.get(f"{base_url}/health")
        print(f"   Status: {response.json()}")
        
        # 2. Submit PGNs for analysis
        print("\n2. Submitting PGN for analysis...")
        response = await client.post(
            f"{base_url}/api/analyze",
            json={"pgns": [sample_pgn]}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Job ID: {result['job_id']}")
            print(f"   Game IDs: {result['game_ids']}")
            game_id = result['game_ids'][0]
            
            # 3. Check status periodically
            print("\n3. Checking analysis status...")
            for i in range(10):
                await asyncio.sleep(2)
                response = await client.get(f"{base_url}/api/games/{game_id}/status")
                status_data = response.json()
                print(f"   Attempt {i+1}: Status = {status_data['status']}, Mistakes = {status_data['mistakes_count']}")
                
                if status_data['status'] in ['completed', 'failed']:
                    break
            
            # 4. Get full analysis results
            print("\n4. Fetching full analysis results...")
            response = await client.get(f"{base_url}/api/games/{game_id}")
            if response.status_code == 200:
                game_data = response.json()
                print(f"   Game status: {game_data['status']}")
                print(f"   Total mistakes found: {len(game_data['mistakes'])}")
                
                # Print mistakes
                for mistake in game_data['mistakes'][:3]:  # Show first 3 mistakes
                    print(f"\n   Mistake at move {mistake['move_number']}:")
                    print(f"   - Move: {mistake['move_san']}")
                    print(f"   - Eval drop: {mistake['eval_drop']/100:.2f} pawns")
                    if mistake['ai_analysis']:
                        print(f"   - Analysis: {mistake['ai_analysis']}")
        else:
            print(f"   Error: {response.status_code} - {response.text}")


if __name__ == "__main__":
    asyncio.run(main())
