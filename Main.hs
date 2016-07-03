{-# LANGUAGE OverloadedStrings #-}

{- |
   Module          : GititWikiImporter.Main
   Copyright       : Copyright (C) 2016 Jacob Jonsson
   License         : BSD 3

   Maintainer      : Jacob Jonsson
   Stability       : alpha

   This executable is intended for migrating from PmWiki to Gitit.
   It could possibly also serve as a foundation to extend for more
   generic wiki migrations. -}

module Main where

import System.Environment ( getArgs, getProgName )
import System.FilePath (FilePath, (</>), takeFileName)
import System.FilePath.Find
import Data.List ( isInfixOf, splitAt )

import Data.WikiPageConverter

main :: IO ()
main = do
  args <- getArgs
  bootstrap args


bootstrap :: [String] -> IO ()
bootstrap (inDir:outDir:patterns) =
  let getRevs :: [FilePath] -> IO [IO [Revision]]
      getRevs = return . map findRevisions

      commitRevsWithNames :: [IO [Revision]] -> [FilePath] -> IO ()
      commitRevsWithNames [] _ = return ()
      commitRevsWithNames (_:_) [] = error "commitRevsWithNames: Not enough filenames to the revisions."
      commitRevsWithNames (ioR:rs) (f:fs) = do
        rev <- ioR
        commitRevs rev (outDir </> (takeFileName f) ++ ".page")
        commitRevsWithNames rs fs

      replaceChar :: Char -> Char -> String -> String
      replaceChar m r str = map (\c -> if c == m then r else c) str

  in do
    files <- findAllMatchingSubstrings patterns inDir
    revs <- getRevs files
    commitRevsWithNames revs (map (replaceChar '.' '/') files)
bootstrap _ = printHelp

printHelp :: IO ()
printHelp =
  let help prg =
        prg ++ "\n" ++ replicate 40 '=' ++ "\n\n" ++
        "Usage: " ++ prg ++ " SOURCE DESTINATION [PATTERN]\n\n" ++
        prg ++ " tries to read files from source dir and convert them to wiki page revisions.\n" ++
        "These wiki page revisions will then be saved in the destination directory and committed with the extracted metadata.\n\n" ++
        "If patterns are supplied to " ++ prg ++ " it will only try to read files that match the pattern.\n" ++
        "Patterns can be file names, directories, common substrings or wildcars such as * and **.\n" ++
        "Special characters in patterns:\n" ++
        "*   :   Matches all characters except directory separators.\n" ++
        "**  :   Matches all characters including directory separators.\n" ++
        "\\   :   Escapes a character that otherwise has another meaning.\n" ++
        "        To get the literal '\' use \\\\."
            in do
    progName <- getProgName
    putStrLn (help progName)


findAllMatchingSubstrings :: [String] -> FilePath -> IO [FilePath]
findAllMatchingSubstrings [] path = findAllMatching always path
findAllMatchingSubstrings ss path = findAllMatching pred path
  where pred = (filePath ~~? "**(" ++ foldl1 (\a b -> a ++ "|" ++ b) ss ++ ")**")

-- | Finds all files in directories and subdirectories that are not ignored
--   and that satisfies the predicate
findAllMatching :: FindClause Bool -> FilePath -> IO [FilePath]
findAllMatching pred path = find always ((filePath `opNoneOf` ignoredDirs) &&? pred) path
  where opNoneOf = liftOp containsNoneOf

-- | Finds all files in directories and subdirectories that are not ignored
findAllFilesInDir :: FilePath -> IO [FilePath]
findAllFilesInDir path = findAllMatching always path

-- | Ignored directories, content in these directories will not be found by
--   findAllFilesInDir
ignoredDirs :: [FilePath]
ignoredDirs = ["stack-work", "git"]

-- | Predicate that checks that a bunch of strings / file paths are not infixes
--   of the file path to check.
containsNoneOf :: FilePath -> [FilePath] -> Bool
containsNoneOf f ignores = foldl (\b ig -> b && f `notContains` ig) True ignores
  where notContains = (\f infx  -> not (isInfixOf infx f))
